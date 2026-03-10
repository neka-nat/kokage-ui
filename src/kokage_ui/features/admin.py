"""Admin dashboard generator.

Provides AdminSite and ModelAdmin for auto-generating Django-admin-like
management interfaces from Pydantic models + Storage backends.
"""

from __future__ import annotations

import csv
import inspect
import io
import math
import urllib.parse
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.responses import RedirectResponse

from kokage_ui.components import Alert, Badge, Breadcrumb, Card, NavBar, Stat, Stats
from kokage_ui.data.crud import Storage, _process_bool_fields
from kokage_ui.data.datagrid import ColumnFilter, DataGrid, DataGridState
from kokage_ui.elements import A, Component, Div, H1, H2, Li, P, Small, Span, Strong, Ul
from kokage_ui.features.auth import UserMenu
from kokage_ui.features.charts import Chart, ChartData, Dataset
from kokage_ui.features.theme import ThemeSwitcher
from kokage_ui.htmx import ConfirmDelete
from kokage_ui.models import ModelDetail, ModelForm, _filter_fields
from kokage_ui.page import Page


def _to_html_string_lazy(result: Any) -> str:
    """Convert to HTML string with lazy import to avoid circular imports."""
    from kokage_ui.core import _to_html_string

    return _to_html_string(result)


def _toast_url(base_url: str, message: str, toast_type: str = "success") -> str:
    """Append toast query parameters to a URL."""
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}_toast={urllib.parse.quote(message)}&_toast_type={toast_type}"


# ========================================
# Activity Log
# ========================================

_ACTIVITY_COLORS = {
    "created": "success",
    "updated": "warning",
    "deleted": "error",
}


class ActivityEntry(BaseModel):
    """A single activity log entry."""

    action: str  # "created", "updated", "deleted"
    model_name: str
    item_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: str = ""


class ActivityLog:
    """In-memory ring buffer for recent admin operations."""

    def __init__(self, max_entries: int = 50) -> None:
        self._entries: deque[ActivityEntry] = deque(maxlen=max_entries)

    def record(
        self, action: str, model_name: str, item_id: str, user: str = ""
    ) -> None:
        self._entries.appendleft(
            ActivityEntry(
                action=action, model_name=model_name, item_id=item_id, user=user
            )
        )

    @property
    def entries(self) -> list[ActivityEntry]:
        return list(self._entries)

    def recent(self, n: int = 10) -> list[ActivityEntry]:
        return list(self._entries)[:n]


class ModelAdmin(BaseModel):
    """Configuration for a registered model in AdminSite.

    Args:
        model: Pydantic BaseModel class.
        storage: Storage backend for CRUD operations.
        name: URL slug (default: model.__name__.lower()).
        title: Display name (default: model.__name__ + "s").
        icon: Sidebar icon text (default: first letter of model name).
        list_fields: Fields to show in list view (None = all).
        search_fields: Fields to search (None = all via storage).
        form_exclude: Fields to exclude from forms.
        list_exclude: Fields to exclude from list view.
        per_page: Items per page in list view.
        id_field: Name of the ID field.
        filters: Column filter definitions for DataGrid (field_name → ColumnFilter).
        actions: Custom bulk actions as (label, handler) tuples.
            Handler receives (selected_ids: list[str], storage: Storage) → None.
        dashboard_widgets: List of callables returning Components for model dashboard.
            Each callable receives (items: list, total: int) → Component.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    model: type[BaseModel]
    storage: Storage
    name: str = ""
    title: str = ""
    icon: str = ""
    list_fields: list[str] | None = None
    search_fields: list[str] | None = None
    form_exclude: list[str] | None = None
    list_exclude: list[str] | None = None
    per_page: int = 20
    id_field: str = "id"
    filters: dict[str, ColumnFilter] | None = None
    actions: list[tuple[str, Callable]] | None = None
    dashboard_widgets: list[Callable] | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.name:
            self.name = self.model.__name__.lower()
        if not self.title:
            self.title = self.model.__name__ + "s"
        if not self.icon:
            self.icon = self.model.__name__[0].upper()


class AdminSite:
    """Admin dashboard generator.

    Registers Pydantic models and auto-generates a full admin interface
    with list, create, detail, edit, and delete views.

    Args:
        app: FastAPI application instance.
        prefix: URL prefix for admin routes (default: "/admin").
        title: Site title displayed in navbar (default: "Admin").
        auth_check: Optional callable(Request) -> user | None for auth.
        theme: DaisyUI theme name (default: "corporate").
        logout_url: Logout URL for user menu (default: "/logout").
    """

    def __init__(
        self,
        app: FastAPI,
        prefix: str = "/admin",
        title: str = "Admin",
        auth_check: Callable | None = None,
        theme: str = "corporate",
        logout_url: str = "/logout",
    ) -> None:
        self.app = app
        self.prefix = prefix.rstrip("/")
        self.title = title
        self.auth_check = auth_check
        self.theme = theme
        self.logout_url = logout_url
        self._registrations: list[ModelAdmin] = []
        self.activity_log = ActivityLog()
        self._register_dashboard_routes()

    def register(self, model: type[BaseModel], *, storage: Storage, **kwargs: Any) -> None:
        """Register a model with the admin site.

        Args:
            model: Pydantic BaseModel class.
            storage: Storage backend.
            **kwargs: Additional ModelAdmin options.
        """
        admin = ModelAdmin(model=model, storage=storage, **kwargs)
        self._registrations.append(admin)
        self._register_model_routes(admin)

    # ========================================
    # Layout helpers
    # ========================================

    def _build_sidebar(
        self,
        active_model: str | None = None,
        counts: dict[str, int] | None = None,
    ) -> Component:
        """Build the sidebar navigation menu.

        Args:
            active_model: Currently active model name (for highlight).
            counts: Dict of model_name → item count (for badges).
        """
        counts = counts or {}
        items: list[Any] = [
            Li(
                A(
                    Span(self.title[0], cls="text-lg font-bold"),
                    "Dashboard",
                    href=f"{self.prefix}/",
                    cls="font-semibold" if active_model is None else "",
                )
            ),
        ]
        for reg in self._registrations:
            is_active = active_model == reg.name
            link_children: list[Any] = [
                Span(reg.icon, cls="text-lg font-bold"),
                reg.title,
            ]
            count = counts.get(reg.name)
            if count is not None:
                link_children.append(
                    Badge(str(count), color="neutral", cls="badge-sm")
                )
            items.append(
                Li(
                    A(
                        *link_children,
                        href=f"{self.prefix}/{reg.name}/",
                        cls="active" if is_active else "",
                    )
                )
            )
        return Ul(
            *items,
            cls="menu bg-base-200 w-56 min-h-screen p-4 pt-20",
        )

    def _build_navbar(self, user: Any = None) -> Component:
        """Build the top navigation bar."""
        title_link = A(self.title, href=f"{self.prefix}/", cls="text-xl font-bold")
        end_children: list[Any] = [ThemeSwitcher(current=self.theme)]
        if user is not None:
            username = ""
            if isinstance(user, dict):
                username = user.get("username", str(user))
            elif hasattr(user, "username"):
                username = user.username
            else:
                username = str(user)
            end_children.append(
                UserMenu(username=username, logout_url=self.logout_url)
            )
        return NavBar(
            start=title_link,
            end=Div(*end_children, cls="flex items-center gap-2"),
            cls="navbar bg-base-100 shadow-sm fixed top-0 z-50",
        )

    def _admin_page(
        self,
        content: Any,
        title: str,
        active_model: str | None = None,
        breadcrumb_items: list[tuple[str, str | None]] | None = None,
        user: Any = None,
        counts: dict[str, int] | None = None,
    ) -> Page:
        """Wrap content in the admin layout."""
        navbar = self._build_navbar(user=user)
        sidebar = self._build_sidebar(active_model=active_model, counts=counts)

        body_children: list[Any] = []
        if breadcrumb_items:
            body_children.append(Breadcrumb(items=breadcrumb_items))
        body_children.append(content)

        main_content = Div(*body_children, cls="p-6 flex-1")
        layout = Div(
            navbar,
            Div(sidebar, main_content, cls="flex pt-16"),
        )
        return Page(layout, title=f"{title} - {self.title}", theme=self.theme, include_toast=True, include_chartjs=True)

    # ========================================
    # Auth
    # ========================================

    def _wrap_auth(self, handler: Callable) -> Callable:
        """Wrap a route handler with auth check."""
        if self.auth_check is None:
            return handler

        auth_check = self.auth_check

        import functools

        @functools.wraps(handler)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = kwargs.get("request")
            if request is None and args:
                request = args[0]
            user = auth_check(request)
            if inspect.isawaitable(user):
                user = await user
            if user is None:
                next_url = str(request.url)
                return RedirectResponse(f"/login?next={urllib.parse.quote(next_url)}", status_code=302)
            request.state.user = user
            return await handler(*args, **kwargs)

        return wrapper

    # ========================================
    # Route registration
    # ========================================

    def _render_activity_feed(self, n: int = 10) -> Component:
        """Render the recent activity feed."""
        entries = self.activity_log.recent(n)
        if not entries:
            return Card(
                P("No recent activity.", cls="text-base-content/60"),
                title="Recent Activity",
            )

        items: list[Any] = []
        for entry in entries:
            color = _ACTIVITY_COLORS.get(entry.action, "info")
            time_str = entry.timestamp.strftime("%H:%M:%S")
            user_str = f" by {entry.user}" if entry.user else ""
            items.append(
                Div(
                    Div(
                        Badge(entry.action, color=color, cls="badge-sm"),
                        Strong(f" {entry.model_name}", cls="text-sm"),
                        Span(f" #{entry.item_id}", cls="text-sm text-base-content/60"),
                        cls="flex items-center gap-1",
                    ),
                    Small(f"{time_str}{user_str}", cls="text-xs text-base-content/50"),
                    cls="flex items-center justify-between py-1 border-b border-base-200 last:border-0",
                )
            )

        return Card(Div(*items), title="Recent Activity")

    def _register_dashboard_routes(self) -> None:
        """Register the main dashboard route."""
        site = self

        async def dashboard(request: Request) -> HTMLResponse:
            user = getattr(request.state, "user", None)

            # Collect stats for each model
            stat_components: list[Any] = []
            model_cards: list[Any] = []
            counts: dict[str, int] = {}
            chart_labels: list[str] = []
            chart_values: list[int] = []
            chart_colors = [
                "#36a2eb", "#ff6384", "#ffce56", "#4bc0c0", "#9966ff",
                "#ff9f40", "#c9cbcf", "#e7e9ed",
            ]

            for i, reg in enumerate(site._registrations):
                _, total = await reg.storage.list(skip=0, limit=1)
                counts[reg.name] = total
                stat_components.append(
                    Stat(title=reg.title, value=str(total))
                )
                chart_labels.append(reg.title)
                chart_values.append(total)
                model_cards.append(
                    Card(
                        Span(f"{total} items", cls="text-sm opacity-70"),
                        title=reg.title,
                        actions=[
                            A("View", href=f"{site.prefix}/{reg.name}/", cls="btn btn-primary btn-sm"),
                            A("Create New", href=f"{site.prefix}/{reg.name}/new", cls="btn btn-ghost btn-sm"),
                        ],
                    )
                )

            # Overview chart
            overview_chart = Chart(
                type="bar",
                data=ChartData(
                    labels=chart_labels,
                    datasets=[
                        Dataset(
                            label="Records",
                            data=chart_values,
                            backgroundColor=chart_colors[: len(chart_labels)],
                        ),
                    ],
                ),
                options={"plugins": {"legend": {"display": False}}, "scales": {"y": {"beginAtZero": True}}},
                height="250px",
            )

            # Custom dashboard widgets from all registrations
            custom_widgets: list[Any] = []
            for reg in site._registrations:
                if reg.dashboard_widgets:
                    items, total = await reg.storage.list(skip=0, limit=100)
                    for widget_fn in reg.dashboard_widgets:
                        result = widget_fn(items, total)
                        if inspect.isawaitable(result):
                            result = await result
                        custom_widgets.append(result)

            # Activity feed
            activity_feed = site._render_activity_feed()

            # Build content
            children: list[Any] = [
                H1("Dashboard", cls="text-3xl font-bold mb-6"),
                Stats(*stat_components, cls="mb-6") if stat_components else Div(),
                Div(
                    Card(overview_chart, title="Overview"),
                    activity_feed,
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6",
                ),
                Div(*model_cards, cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"),
            ]

            if custom_widgets:
                children.append(
                    Div(
                        H2("Widgets", cls="text-2xl font-bold mt-6 mb-4"),
                        Div(*custom_widgets, cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"),
                    )
                )

            content = Div(*children)

            return HTMLResponse(
                content=_to_html_string_lazy(
                    site._admin_page(
                        content,
                        "Dashboard",
                        breadcrumb_items=[("Admin", None)],
                        user=user,
                        counts=counts,
                    )
                )
            )

        handler = self._wrap_auth(dashboard)
        self.app.add_api_route(
            f"{self.prefix}/",
            handler,
            methods=["GET"],
            response_class=HTMLResponse,
        )

    def _register_model_routes(self, admin: ModelAdmin) -> None:
        """Register all CRUD routes for a model."""
        site = self
        prefix = self.prefix
        name = admin.name
        model = admin.model
        storage = admin.storage
        id_field = admin.id_field
        form_exclude = list(set([id_field] + (admin.form_exclude or [])))
        list_exclude = admin.list_exclude or []
        grid_filters = admin.filters

        # Build bulk actions: default Delete + custom actions
        bulk_actions: list[tuple[str, str]] = [
            ("Delete Selected", f"{prefix}/{name}/_bulk_delete"),
        ]
        custom_actions = admin.actions or []
        for i, (label, _handler_fn) in enumerate(custom_actions):
            bulk_actions.append((label, f"{prefix}/{name}/_action/{i}"))

        base_breadcrumb: list[tuple[str, str | None]] = [
            ("Admin", f"{prefix}/"),
            (admin.title, f"{prefix}/{name}/"),
        ]

        def _render_actions(row: BaseModel) -> Component:
            """Render Edit + Delete action buttons for a table row."""
            row_id = getattr(row, id_field)
            return Div(
                A("Edit", href=f"{prefix}/{name}/{row_id}/edit", cls="btn btn-warning btn-xs"),
                ConfirmDelete(
                    "Delete",
                    url=f"{prefix}/{name}/{row_id}",
                    confirm_message=f"Delete this {model.__name__}?",
                    target="body",
                    cls="btn btn-error btn-outline btn-xs ml-2",
                ),
                cls="flex gap-1",
            )

        def _build_grid(
            items: list[BaseModel],
            total: int,
            state: DataGridState,
        ) -> DataGrid:
            """Build a DataGrid with shared config."""
            total_pages = max(1, math.ceil(total / admin.per_page))
            return DataGrid(
                model,
                items,
                data_url=f"{prefix}/{name}/_list",
                grid_id=f"{name}-grid",
                exclude=list_exclude,
                include=admin.list_fields,
                sort_field=state.sort_field,
                sort_order=state.sort_order,
                filters=grid_filters,
                filter_values=state.filter_values,
                visible_columns=state.visible_columns,
                page=state.page,
                total_pages=total_pages,
                total_items=total,
                per_page=admin.per_page,
                bulk_actions=bulk_actions,
                csv_url=f"{prefix}/{name}/_csv",
                id_field=id_field,
                cell_renderers={id_field: lambda v: A(str(v), href=f"{prefix}/{name}/{v}")},
                extra_columns={"Actions": _render_actions},
                zebra=True,
            )

        def _get_username(request: Request) -> str:
            """Extract username from request state."""
            user = getattr(request.state, "user", None)
            if user is None:
                return ""
            if isinstance(user, dict):
                return user.get("username", "")
            return getattr(user, "username", str(user))

        # --- GET {prefix}/{name}/ — List page ---
        async def list_page(request: Request) -> HTMLResponse:
            user = getattr(request.state, "user", None)
            state = DataGridState.from_request(request)
            skip = (state.page - 1) * admin.per_page
            search = request.query_params.get("q") or None
            items, total = await storage.list(skip=skip, limit=admin.per_page, search=search)

            grid = _build_grid(items, total, state)

            content = Div(
                Div(
                    H1(admin.title, cls="text-3xl font-bold"),
                    A("Create New", href=f"{prefix}/{name}/new", cls="btn btn-primary btn-sm"),
                    cls="flex items-center justify-between mb-6",
                ),
                grid,
            )

            return HTMLResponse(
                content=_to_html_string_lazy(
                    site._admin_page(
                        content,
                        admin.title,
                        active_model=name,
                        breadcrumb_items=base_breadcrumb[:-1] + [(admin.title, None)],
                        user=user,
                    )
                )
            )

        # --- GET {prefix}/{name}/_list — List fragment (htmx) ---
        async def list_fragment(request: Request) -> HTMLResponse:
            state = DataGridState.from_request(request)
            skip = (state.page - 1) * admin.per_page
            search = request.query_params.get("q") or None
            items, total = await storage.list(skip=skip, limit=admin.per_page, search=search)

            grid = _build_grid(items, total, state)
            return HTMLResponse(content=_to_html_string_lazy(grid))

        # --- POST {prefix}/{name}/_bulk_delete — Bulk delete ---
        async def bulk_delete(request: Request) -> HTMLResponse:
            form_data = await request.form()
            selected = form_data.getlist("selected")
            username = _get_username(request)
            for item_id in selected:
                await storage.delete(str(item_id))
                site.activity_log.record("deleted", model.__name__, str(item_id), user=username)

            # Re-render list fragment
            items, total = await storage.list(skip=0, limit=admin.per_page)
            state = DataGridState(page=1)
            grid = _build_grid(items, total, state)
            return HTMLResponse(content=_to_html_string_lazy(grid))

        # --- POST {prefix}/{name}/_action/{index} — Custom action ---
        async def custom_action_handler(request: Request, index: int) -> HTMLResponse:
            form_data = await request.form()
            selected = list(form_data.getlist("selected"))

            if 0 <= index < len(custom_actions):
                _, handler_fn = custom_actions[index]
                result = handler_fn(selected, storage)
                if inspect.isawaitable(result):
                    await result

            # Re-render list fragment
            items, total = await storage.list(skip=0, limit=admin.per_page)
            state = DataGridState(page=1)
            grid = _build_grid(items, total, state)
            return HTMLResponse(content=_to_html_string_lazy(grid))

        # --- GET {prefix}/{name}/_csv — CSV export ---
        async def csv_export(request: Request) -> StreamingResponse:
            items, _ = await storage.list(skip=0, limit=100000)
            fields = _filter_fields(model, admin.list_fields, list_exclude)
            field_names = [n for n, _ in fields]

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(field_names)
            for item in items:
                writer.writerow([getattr(item, f) for f in field_names])

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{name}.csv"'},
            )

        # --- GET {prefix}/{name}/new — Create form page ---
        async def create_page(request: Request) -> HTMLResponse:
            user = getattr(request.state, "user", None)
            form = ModelForm(
                model,
                action=f"{prefix}/{name}/new",
                method="post",
                submit_text="Create",
                submit_color="primary",
                exclude=form_exclude,
                hx_post=f"{prefix}/{name}/new",
                hx_target="#form-container",
            )

            content = Div(
                H1(f"New {model.__name__}", cls="text-3xl font-bold mb-6"),
                Div(form, id="form-container", cls="max-w-lg"),
            )

            return HTMLResponse(
                content=_to_html_string_lazy(
                    site._admin_page(
                        content,
                        f"New {model.__name__}",
                        active_model=name,
                        breadcrumb_items=base_breadcrumb + [("New", None)],
                        user=user,
                    )
                )
            )

        # --- POST {prefix}/{name}/new — Create handler ---
        async def create_handler(request: Request) -> Response:
            form_data = await request.form()
            raw_data = dict(form_data)
            _process_bool_fields(model, raw_data, form_data, form_exclude)

            try:
                instance = model.model_validate(raw_data)
                created = await storage.create(instance)
                created_id = getattr(created, id_field)
                site.activity_log.record(
                    "created", model.__name__, str(created_id),
                    user=_get_username(request),
                )
                redirect_url = _toast_url(
                    f"{prefix}/{name}/{created_id}", "Created successfully"
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
                    model,
                    action=f"{prefix}/{name}/new",
                    method="post",
                    submit_text="Create",
                    submit_color="primary",
                    exclude=form_exclude,
                    values=raw_data,
                    errors=error_list,
                    hx_post=f"{prefix}/{name}/new",
                    hx_target="#form-container",
                )
                html = _to_html_string_lazy(form)

                if request.headers.get("hx-request"):
                    return HTMLResponse(content=html, status_code=422)

                user = getattr(request.state, "user", None)
                content = Div(
                    H1(f"New {model.__name__}", cls="text-3xl font-bold mb-6"),
                    Div(form, id="form-container", cls="max-w-lg"),
                )
                return HTMLResponse(
                    content=_to_html_string_lazy(
                        site._admin_page(
                            content,
                            f"New {model.__name__}",
                            active_model=name,
                            breadcrumb_items=base_breadcrumb + [("New", None)],
                            user=user,
                        )
                    ),
                    status_code=422,
                )

        # --- GET {prefix}/{name}/{id} — Detail page ---
        async def detail_page(request: Request, id: str) -> HTMLResponse:
            user = getattr(request.state, "user", None)
            item = await storage.get(id)
            if item is None:
                content = Div(
                    Alert("Not found.", variant="error"),
                )
                return HTMLResponse(
                    content=_to_html_string_lazy(
                        site._admin_page(content, "Not Found", active_model=name, user=user)
                    ),
                    status_code=404,
                )

            detail = ModelDetail(item, title=str(getattr(item, id_field)))
            actions = Div(
                A("Edit", href=f"{prefix}/{name}/{id}/edit", cls="btn btn-warning btn-sm"),
                ConfirmDelete(
                    "Delete",
                    url=f"{prefix}/{name}/{id}",
                    confirm_message=f"Delete this {model.__name__}?",
                    target="body",
                    cls="btn btn-error btn-outline btn-sm ml-2",
                ),
                A("Back to list", href=f"{prefix}/{name}/", cls="btn btn-ghost btn-sm ml-2"),
                cls="mt-4",
            )

            content = Div(detail, actions)

            return HTMLResponse(
                content=_to_html_string_lazy(
                    site._admin_page(
                        content,
                        f"{model.__name__} Detail",
                        active_model=name,
                        breadcrumb_items=base_breadcrumb + [(str(getattr(item, id_field)), None)],
                        user=user,
                    )
                )
            )

        # --- GET {prefix}/{name}/{id}/edit — Edit form page ---
        async def edit_page(request: Request, id: str) -> HTMLResponse:
            user = getattr(request.state, "user", None)
            item = await storage.get(id)
            if item is None:
                content = Div(Alert("Not found.", variant="error"))
                return HTMLResponse(
                    content=_to_html_string_lazy(
                        site._admin_page(content, "Not Found", active_model=name, user=user)
                    ),
                    status_code=404,
                )

            form = ModelForm(
                model,
                action=f"{prefix}/{name}/{id}/edit",
                method="post",
                submit_text="Update",
                submit_color="warning",
                exclude=form_exclude,
                instance=item,
                hx_post=f"{prefix}/{name}/{id}/edit",
                hx_target="#form-container",
            )

            content = Div(
                H1(f"Edit {model.__name__}", cls="text-3xl font-bold mb-6"),
                Div(form, id="form-container", cls="max-w-lg"),
            )

            return HTMLResponse(
                content=_to_html_string_lazy(
                    site._admin_page(
                        content,
                        f"Edit {model.__name__}",
                        active_model=name,
                        breadcrumb_items=base_breadcrumb + [(id, f"{prefix}/{name}/{id}"), ("Edit", None)],
                        user=user,
                    )
                )
            )

        # --- POST {prefix}/{name}/{id}/edit — Edit handler ---
        async def edit_handler(request: Request, id: str) -> Response:
            item = await storage.get(id)
            if item is None:
                return HTMLResponse(content="Not found", status_code=404)

            form_data = await request.form()
            raw_data = dict(form_data)
            _process_bool_fields(model, raw_data, form_data, form_exclude)
            raw_data[id_field] = id

            try:
                instance = model.model_validate(raw_data)
                await storage.update(id, instance)
                site.activity_log.record(
                    "updated", model.__name__, str(id),
                    user=_get_username(request),
                )
                redirect_url = _toast_url(
                    f"{prefix}/{name}/{id}", "Updated successfully"
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
                    model,
                    action=f"{prefix}/{name}/{id}/edit",
                    method="post",
                    submit_text="Update",
                    submit_color="warning",
                    exclude=form_exclude,
                    values=raw_data,
                    errors=error_list,
                    hx_post=f"{prefix}/{name}/{id}/edit",
                    hx_target="#form-container",
                )
                html = _to_html_string_lazy(form)

                if request.headers.get("hx-request"):
                    return HTMLResponse(content=html, status_code=422)

                user = getattr(request.state, "user", None)
                content = Div(
                    H1(f"Edit {model.__name__}", cls="text-3xl font-bold mb-6"),
                    Div(form, id="form-container", cls="max-w-lg"),
                )
                return HTMLResponse(
                    content=_to_html_string_lazy(
                        site._admin_page(
                            content,
                            f"Edit {model.__name__}",
                            active_model=name,
                            breadcrumb_items=base_breadcrumb + [(id, f"{prefix}/{name}/{id}"), ("Edit", None)],
                            user=user,
                        )
                    ),
                    status_code=422,
                )

        # --- DELETE {prefix}/{name}/{id} — Delete handler ---
        async def delete_handler(request: Request, id: str) -> Response:
            deleted = await storage.delete(id)
            if not deleted:
                return HTMLResponse(content="Not found", status_code=404)

            site.activity_log.record(
                "deleted", model.__name__, str(id),
                user=_get_username(request),
            )
            redirect_url = _toast_url(f"{prefix}/{name}/", "Deleted successfully")
            if request.headers.get("hx-request"):
                return Response(
                    status_code=200,
                    headers={"HX-Redirect": redirect_url},
                )
            return Response(
                status_code=303,
                headers={"Location": redirect_url},
            )

        # Register routes — fixed paths before parameterized ones
        route_defs: list[tuple[str, Callable, list[str]]] = [
            (f"{prefix}/{name}/", list_page, ["GET"]),
            (f"{prefix}/{name}/_list", list_fragment, ["GET"]),
            (f"{prefix}/{name}/_bulk_delete", bulk_delete, ["POST"]),
            (f"{prefix}/{name}/_csv", csv_export, ["GET"]),
            (f"{prefix}/{name}/new", create_page, ["GET"]),
            (f"{prefix}/{name}/new", create_handler, ["POST"]),
            (f"{prefix}/{name}/{{id}}", detail_page, ["GET"]),
            (f"{prefix}/{name}/{{id}}/edit", edit_page, ["GET"]),
            (f"{prefix}/{name}/{{id}}/edit", edit_handler, ["POST"]),
            (f"{prefix}/{name}/{{id}}", delete_handler, ["DELETE"]),
        ]

        # Register custom action routes
        for i in range(len(custom_actions)):
            async def _action_route(request: Request, _idx: int = i) -> HTMLResponse:
                return await custom_action_handler(request, _idx)

            route_defs.append(
                (f"{prefix}/{name}/_action/{i}", _action_route, ["POST"])
            )

        for path, handler_fn, methods in route_defs:
            wrapped = self._wrap_auth(handler_fn)
            self.app.add_api_route(
                path,
                wrapped,
                methods=methods,
                response_class=HTMLResponse,
            )
