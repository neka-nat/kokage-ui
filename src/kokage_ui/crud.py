"""CRUD auto-generation from Pydantic models.

Generates list/create/detail/edit/delete routes and UI from a single
Pydantic BaseModel + Storage backend.
"""

from __future__ import annotations

import math
import urllib.parse
import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ValidationError

from kokage_ui.components import Alert
from kokage_ui.elements import A, Button, Component, Div, H1
from kokage_ui.htmx import ConfirmDelete, SearchFilter
from kokage_ui.models import ModelDetail, ModelForm, ModelTable, _resolve_annotation

T = TypeVar("T", bound=BaseModel)


# ========================================
# Storage ABC
# ========================================


class Storage(ABC, Generic[T]):
    """Abstract async storage interface for CRUD operations."""

    @abstractmethod
    async def list(
        self, *, skip: int = 0, limit: int = 20, search: str | None = None
    ) -> tuple[list[T], int]:
        """Return (items, total_count)."""

    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Get a single item by ID."""

    @abstractmethod
    async def create(self, data: T) -> T:
        """Create a new item. Returns the created item (with ID assigned)."""

    @abstractmethod
    async def update(self, id: str, data: T) -> T | None:
        """Update an existing item. Returns updated item or None if not found."""

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an item. Returns True if deleted, False if not found."""


# ========================================
# InMemoryStorage
# ========================================


class InMemoryStorage(Storage[T]):
    """In-memory dict-based storage with UUID auto-assignment.

    Args:
        model: Pydantic model class.
        initial: Optional list of initial items.
        id_field: Name of the ID field (default: "id").
    """

    def __init__(
        self,
        model: type[T],
        *,
        initial: list[T] | None = None,
        id_field: str = "id",
    ) -> None:
        self._model = model
        self._id_field = id_field
        self._data: dict[str, T] = {}

        if initial:
            for item in initial:
                item_id = getattr(item, id_field, "") or ""
                if not item_id:
                    item_id = str(uuid.uuid4())[:8]
                    item = item.model_copy(update={id_field: item_id})
                self._data[item_id] = item

    async def list(
        self, *, skip: int = 0, limit: int = 20, search: str | None = None
    ) -> tuple[list[T], int]:
        items = list(self._data.values())
        if search:
            search_lower = search.lower()
            items = [
                item
                for item in items
                if any(
                    search_lower in str(getattr(item, f, "")).lower()
                    for f in self._model.model_fields
                )
            ]
        total = len(items)
        return items[skip : skip + limit], total

    async def get(self, id: str) -> T | None:
        return self._data.get(id)

    async def create(self, data: T) -> T:
        item_id = getattr(data, self._id_field, "") or ""
        if not item_id:
            item_id = str(uuid.uuid4())[:8]
            data = data.model_copy(update={self._id_field: item_id})
        self._data[item_id] = data
        return data

    async def update(self, id: str, data: T) -> T | None:
        if id not in self._data:
            return None
        data = data.model_copy(update={self._id_field: id})
        self._data[id] = data
        return data

    async def delete(self, id: str) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False


# ========================================
# Pagination Component
# ========================================


class Pagination(Component):
    """DaisyUI join button group for pagination with htmx support.

    Args:
        current_page: Current page number (1-indexed).
        total_pages: Total number of pages.
        base_url: URL template for page links.
        search: Optional search query to preserve in URLs.
    """

    tag = "div"

    def __init__(
        self,
        *,
        current_page: int,
        total_pages: int,
        base_url: str,
        target: str = "#table-container",
        search: str | None = None,
        **attrs: Any,
    ) -> None:
        if total_pages <= 1:
            super().__init__(**attrs)
            return

        # Show at most 7 page buttons: first, last, current, and neighbors
        max_visible = 7
        if total_pages <= max_visible:
            visible = list(range(1, total_pages + 1))
        else:
            visible_set = {1, total_pages}
            half = (max_visible - 2) // 2
            start = max(2, current_page - half)
            end = min(total_pages - 1, current_page + half)
            # Adjust if near edges
            if end - start < max_visible - 3:
                if start == 2:
                    end = min(total_pages - 1, start + max_visible - 3)
                else:
                    start = max(2, end - (max_visible - 3))
            visible_set.update(range(start, end + 1))
            visible = sorted(visible_set)

        buttons: list[Any] = []
        for page_num in visible:
            url = f"{base_url}?page={page_num}"
            if search:
                url += f"&q={search}"
            btn_cls = "join-item btn btn-sm"
            if page_num == current_page:
                btn_cls += " btn-active"
            buttons.append(
                Button(
                    str(page_num),
                    cls=btn_cls,
                    hx_get=url,
                    hx_target=target,
                )
            )

        attrs["cls"] = "join mt-4"
        super().__init__(*buttons, **attrs)


# ========================================
# CRUDRouter
# ========================================


_to_html_string_fn: Callable | None = None


def _to_html_string_lazy(result: Any) -> str:
    """Convert to HTML string with lazy import to avoid circular imports."""
    global _to_html_string_fn
    if _to_html_string_fn is None:
        from kokage_ui.core import _to_html_string

        _to_html_string_fn = _to_html_string
    return _to_html_string_fn(result)


def _process_bool_fields(
    model: type[BaseModel],
    raw_data: dict[str, Any],
    form_data: Any,
    exclude: list[str],
) -> None:
    """Handle bool fields: unchecked checkboxes are absent from form data."""
    for field_name, field_info in model.model_fields.items():
        if field_name in exclude:
            continue
        base_type, _ = _resolve_annotation(field_info.annotation)
        if base_type is bool:
            raw_data[field_name] = field_name in form_data


class CRUDRouter(Generic[T]):
    """Auto-register all CRUD routes for a Pydantic model.

    Args:
        app: FastAPI application.
        prefix: URL prefix (e.g., "/users").
        model: Pydantic BaseModel class.
        storage: Storage backend.
        id_field: Name of the ID field.
        per_page: Items per page.
        title: Display title (defaults to model name + "s").
        exclude_fields: Fields to exclude from all views.
        table_exclude: Fields to exclude from table view.
        form_exclude: Fields to exclude from forms.
        page_wrapper: Optional callable(content, title) → Page for custom layout.
        theme: DaisyUI theme name.
    """

    def __init__(
        self,
        app: FastAPI,
        prefix: str,
        model: type[T],
        storage: Storage[T],
        *,
        id_field: str = "id",
        per_page: int = 20,
        title: str | None = None,
        exclude_fields: list[str] | None = None,
        table_exclude: list[str] | None = None,
        form_exclude: list[str] | None = None,
        page_wrapper: Callable[..., Any] | None = None,
        theme: str = "light",
    ) -> None:
        self.app = app
        self.prefix = prefix.rstrip("/")
        self.model = model
        self.storage = storage
        self.id_field = id_field
        self.per_page = per_page
        self.title = title or f"{model.__name__}s"
        self.page_wrapper = page_wrapper
        self.theme = theme

        # Cache computed exclude lists
        _exclude = exclude_fields or []
        self._table_exclude = list(set(_exclude + (table_exclude or [])))
        self._form_exclude = list(set(_exclude + (form_exclude or []) + [id_field]))

        self._register_routes()

    def _get_table_exclude(self) -> list[str]:
        return self._table_exclude

    def _get_form_exclude(self) -> list[str]:
        return self._form_exclude

    def _wrap_page(self, content: Any, page_title: str) -> Any:
        if self.page_wrapper:
            return self.page_wrapper(content, page_title)
        from kokage_ui.page import Page

        return Page(content, title=page_title, theme=self.theme, include_toast=True)

    @staticmethod
    def _toast_url(base_url: str, message: str, toast_type: str = "success") -> str:
        """Append toast query parameters to a URL."""
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}_toast={urllib.parse.quote(message)}&_toast_type={toast_type}"

    def _render_actions(self, row: T) -> Component:
        """Render Edit + Delete action buttons for a table row."""
        row_id = getattr(row, self.id_field)
        return Div(
            A("Edit", href=f"{self.prefix}/{row_id}/edit", cls="btn btn-warning btn-xs"),
            ConfirmDelete(
                "Delete",
                url=f"{self.prefix}/{row_id}",
                confirm_message=f"Delete this {self.model.__name__}?",
                target="body",
                cls="btn btn-error btn-outline btn-xs ml-2",
            ),
            cls="flex gap-1",
        )

    def _build_list_table(
        self,
        items: list[T],
        total: int,
        page: int,
        search: str | None,
    ) -> Component:
        """Build the table + pagination fragment."""
        total_pages = max(1, math.ceil(total / self.per_page))
        table_exclude = self._get_table_exclude()

        # Build cell renderers: make ID field a link to detail page
        cell_renderers: dict[str, Callable[[Any], Any]] = {
            self.id_field: lambda v: A(str(v), href=f"{self.prefix}/{v}"),
        }

        table = ModelTable(
            self.model,
            rows=items,
            exclude=table_exclude,
            zebra=True,
            cell_renderers=cell_renderers,
            extra_columns={"Actions": self._render_actions},
        )

        pagination = Pagination(
            current_page=page,
            total_pages=total_pages,
            base_url=f"{self.prefix}/_list",
            target="#table-container",
            search=search,
        )

        return Div(table, pagination, id="table-container")

    def _register_routes(self) -> None:
        prefix = self.prefix
        app = self.app
        router = self

        # --- GET {prefix} — List page ---
        async def list_page(request: Request, page: int = 1, q: str = "") -> HTMLResponse:
            skip = (page - 1) * router.per_page
            items, total = await router.storage.list(
                skip=skip, limit=router.per_page, search=q or None
            )
            table_fragment = router._build_list_table(items, total, page, q or None)

            search_input = SearchFilter(
                url=f"{prefix}/_list",
                target="#table-container",
                placeholder=f"Search {router.title.lower()}...",
                cls="input input-bordered w-full mb-4",
            )

            content = Div(
                H1(router.title, cls="text-3xl font-bold mb-6"),
                Div(
                    A("New", href=f"{prefix}/new", cls="btn btn-primary btn-sm"),
                    cls="mb-4",
                ),
                search_input,
                table_fragment,
                cls="container mx-auto p-4",
            )

            page_obj = router._wrap_page(content, router.title)
            return HTMLResponse(content=_to_html_string_lazy(page_obj))

        app.add_api_route(
            prefix,
            list_page,
            methods=["GET"],
            response_class=HTMLResponse,
        )

        # --- GET {prefix}/_list — Table fragment (htmx) ---
        async def list_fragment(
            request: Request, page: int = 1, q: str = ""
        ) -> HTMLResponse:
            skip = (page - 1) * router.per_page
            items, total = await router.storage.list(
                skip=skip, limit=router.per_page, search=q or None
            )
            table_fragment = router._build_list_table(items, total, page, q or None)
            return HTMLResponse(content=_to_html_string_lazy(table_fragment))

        app.add_api_route(
            f"{prefix}/_list",
            list_fragment,
            methods=["GET"],
            response_class=HTMLResponse,
        )

        # --- GET {prefix}/new — Create form page ---
        async def create_page(request: Request) -> HTMLResponse:
            form = ModelForm(
                router.model,
                action=f"{prefix}/new",
                method="post",
                submit_text="Create",
                submit_color="primary",
                exclude=router._get_form_exclude(),
                hx_post=f"{prefix}/new",
                hx_target="#form-container",
            )

            content = Div(
                H1(f"New {router.model.__name__}", cls="text-3xl font-bold mb-6"),
                Div(form, id="form-container", cls="max-w-lg"),
                cls="container mx-auto p-4",
            )

            page_obj = router._wrap_page(content, f"New {router.model.__name__}")
            return HTMLResponse(content=_to_html_string_lazy(page_obj))

        # --- POST {prefix}/new — Create handler ---
        async def create_handler(request: Request) -> Response:
            form_data = await request.form()
            raw_data = dict(form_data)
            _process_bool_fields(router.model, raw_data, form_data, router._get_form_exclude())

            try:
                instance = router.model.model_validate(raw_data)
                created = await router.storage.create(instance)
                created_id = getattr(created, router.id_field)
                redirect_url = router._toast_url(
                    f"{prefix}/{created_id}", "Created successfully"
                )

                # htmx request → HX-Redirect header
                if request.headers.get("hx-request"):
                    return Response(
                        status_code=200,
                        headers={"HX-Redirect": redirect_url},
                    )
                # Normal form → redirect
                return Response(
                    status_code=303,
                    headers={"Location": redirect_url},
                )
            except ValidationError as e:
                error_list = e.errors()
                form = ModelForm(
                    router.model,
                    action=f"{prefix}/new",
                    method="post",
                    submit_text="Create",
                    submit_color="primary",
                    exclude=router._get_form_exclude(),
                    values=raw_data,
                    errors=error_list,
                    hx_post=f"{prefix}/new",
                    hx_target="#form-container",
                )
                html = _to_html_string_lazy(form)

                # htmx request → return form fragment
                if request.headers.get("hx-request"):
                    return HTMLResponse(content=html, status_code=422)

                # Normal request → full page with error form
                content = Div(
                    H1(f"New {router.model.__name__}", cls="text-3xl font-bold mb-6"),
                    Div(form, id="form-container", cls="max-w-lg"),
                    cls="container mx-auto p-4",
                )
                page_obj = router._wrap_page(content, f"New {router.model.__name__}")
                return HTMLResponse(
                    content=_to_html_string_lazy(page_obj), status_code=422
                )

        # Register /new BEFORE /{id} to avoid path conflicts
        app.add_api_route(
            f"{prefix}/new",
            create_page,
            methods=["GET"],
            response_class=HTMLResponse,
        )
        app.add_api_route(
            f"{prefix}/new",
            create_handler,
            methods=["POST"],
        )

        # --- GET {prefix}/{id} — Detail page ---
        async def detail_page(request: Request, id: str) -> HTMLResponse:
            item = await router.storage.get(id)
            if item is None:
                content = Div(
                    Alert("Not found.", variant="error"),
                    cls="container mx-auto p-4",
                )
                page_obj = router._wrap_page(content, "Not Found")
                return HTMLResponse(
                    content=_to_html_string_lazy(page_obj), status_code=404
                )

            detail = ModelDetail(item, title=str(getattr(item, router.id_field)))

            actions = Div(
                A("Edit", href=f"{prefix}/{id}/edit", cls="btn btn-warning btn-sm"),
                ConfirmDelete(
                    "Delete",
                    url=f"{prefix}/{id}",
                    confirm_message=f"Delete this {router.model.__name__}?",
                    target="body",
                    cls="btn btn-error btn-outline btn-sm ml-2",
                ),
                A("Back to list", href=prefix, cls="btn btn-ghost btn-sm ml-2"),
                cls="mt-4",
            )

            content = Div(
                H1(f"{router.model.__name__} Detail", cls="text-3xl font-bold mb-6"),
                detail,
                actions,
                cls="container mx-auto p-4",
            )

            page_obj = router._wrap_page(
                content, f"{router.model.__name__} Detail"
            )
            return HTMLResponse(content=_to_html_string_lazy(page_obj))

        app.add_api_route(
            f"{prefix}/{{id}}",
            detail_page,
            methods=["GET"],
            response_class=HTMLResponse,
        )

        # --- GET {prefix}/{id}/edit — Edit form page ---
        async def edit_page(request: Request, id: str) -> HTMLResponse:
            item = await router.storage.get(id)
            if item is None:
                content = Div(
                    Alert("Not found.", variant="error"),
                    cls="container mx-auto p-4",
                )
                page_obj = router._wrap_page(content, "Not Found")
                return HTMLResponse(
                    content=_to_html_string_lazy(page_obj), status_code=404
                )

            form = ModelForm(
                router.model,
                action=f"{prefix}/{id}/edit",
                method="post",
                submit_text="Update",
                submit_color="warning",
                exclude=router._get_form_exclude(),
                instance=item,
                hx_post=f"{prefix}/{id}/edit",
                hx_target="#form-container",
            )

            content = Div(
                H1(f"Edit {router.model.__name__}", cls="text-3xl font-bold mb-6"),
                Div(form, id="form-container", cls="max-w-lg"),
                cls="container mx-auto p-4",
            )

            page_obj = router._wrap_page(
                content, f"Edit {router.model.__name__}"
            )
            return HTMLResponse(content=_to_html_string_lazy(page_obj))

        # --- POST {prefix}/{id}/edit — Update handler ---
        async def edit_handler(request: Request, id: str) -> Response:
            item = await router.storage.get(id)
            if item is None:
                return HTMLResponse(content="Not found", status_code=404)

            form_data = await request.form()
            raw_data = dict(form_data)
            _process_bool_fields(router.model, raw_data, form_data, router._get_form_exclude())

            # Preserve ID
            raw_data[router.id_field] = id

            try:
                instance = router.model.model_validate(raw_data)
                await router.storage.update(id, instance)
                redirect_url = router._toast_url(
                    f"{prefix}/{id}", "Updated successfully"
                )

                if request.headers.get("hx-request"):
                    return Response(
                        status_code=200,
                        headers={"HX-Redirect": redirect_url},
                    )
                return Response(
                    status_code=303,
                    headers={"Location": redirect_url},
                )
            except ValidationError as e:
                error_list = e.errors()
                form = ModelForm(
                    router.model,
                    action=f"{prefix}/{id}/edit",
                    method="post",
                    submit_text="Update",
                    submit_color="warning",
                    exclude=router._get_form_exclude(),
                    values=raw_data,
                    errors=error_list,
                    hx_post=f"{prefix}/{id}/edit",
                    hx_target="#form-container",
                )
                html = _to_html_string_lazy(form)

                if request.headers.get("hx-request"):
                    return HTMLResponse(content=html, status_code=422)

                content = Div(
                    H1(f"Edit {router.model.__name__}", cls="text-3xl font-bold mb-6"),
                    Div(form, id="form-container", cls="max-w-lg"),
                    cls="container mx-auto p-4",
                )
                page_obj = router._wrap_page(
                    content, f"Edit {router.model.__name__}"
                )
                return HTMLResponse(
                    content=_to_html_string_lazy(page_obj), status_code=422
                )

        app.add_api_route(
            f"{prefix}/{{id}}/edit",
            edit_page,
            methods=["GET"],
            response_class=HTMLResponse,
        )
        app.add_api_route(
            f"{prefix}/{{id}}/edit",
            edit_handler,
            methods=["POST"],
        )

        # --- DELETE {prefix}/{id} — Delete handler ---
        async def delete_handler(request: Request, id: str) -> Response:
            deleted = await router.storage.delete(id)
            if not deleted:
                return HTMLResponse(content="Not found", status_code=404)

            redirect_url = router._toast_url(prefix, "Deleted successfully")
            if request.headers.get("hx-request"):
                return Response(
                    status_code=200,
                    headers={"HX-Redirect": redirect_url},
                )
            return Response(
                status_code=303,
                headers={"Location": redirect_url},
            )

        app.add_api_route(
            f"{prefix}/{{id}}",
            delete_handler,
            methods=["DELETE"],
        )
