"""DataGrid — advanced table with filters, sorting, bulk actions, column toggle, and CSV export.

Server-side rendered via htmx. All state is managed through URL query parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlencode

from pydantic import BaseModel

from kokage_ui.components import _merge_cls
from kokage_ui.elements import (
    A,
    Button,
    Component,
    Div,
    Input,
    Li,
    Option,
    Select,
    Span,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Tr,
    Ul,
)
from kokage_ui.models import _filter_fields, _render_value


@dataclass
class ColumnFilter:
    """Column filter definition.

    Args:
        type: Filter type — "text", "select", or "number_range".
        options: For "select" type: list of (value, label) tuples.
        placeholder: Placeholder text for the filter input.
    """

    type: str = "text"
    options: list[tuple[str, str]] | None = None
    placeholder: str = ""


@dataclass
class DataGridState:
    """Parse grid state from request query parameters.

    Query params:
        sort: Field name to sort by.
        order: "asc" or "desc".
        page: Page number (1-indexed).
        f_*: Filter values (e.g. f_name=alice).
        col: Visible column names (repeated param).
    """

    sort_field: str | None = None
    sort_order: str = "asc"
    page: int = 1
    filter_values: dict[str, str] = field(default_factory=dict)
    visible_columns: list[str] | None = None

    @classmethod
    def from_request(cls, request: Any) -> DataGridState:
        """Create DataGridState from a Starlette/FastAPI Request object."""
        params = request.query_params
        sort_field = params.get("sort") or None
        sort_order = params.get("order", "asc")
        if sort_order not in ("asc", "desc"):
            sort_order = "asc"

        try:
            page = int(params.get("page", "1"))
        except (ValueError, TypeError):
            page = 1
        if page < 1:
            page = 1

        # Collect filter values (f_* params)
        filter_values: dict[str, str] = {}
        for key in params:
            if key.startswith("f_"):
                val = params[key]
                if val:
                    filter_values[key] = val

        # Collect visible columns (repeated "col" param)
        cols = params.getlist("col")
        visible_columns = cols if cols else None

        return cls(
            sort_field=sort_field,
            sort_order=sort_order,
            page=page,
            filter_values=filter_values,
            visible_columns=visible_columns,
        )

    @property
    def clean_filters(self) -> dict[str, str]:
        """Return filter values with f_ prefix removed and empty values excluded."""
        return {
            k[2:]: v for k, v in self.filter_values.items() if v
        }


class DataGrid(Component):
    """Advanced data grid with sorting, filtering, bulk actions, column toggle, and CSV export.

    All state is managed via URL query parameters. Three interaction patterns:
    1. Pre-built URLs (sort headers, pagination, column toggles)
    2. hx-include (filter inputs send all filter values + hidden state)
    3. hx-post (bulk actions send selected checkbox IDs)

    Args:
        model: Pydantic BaseModel class defining columns.
        rows: List of model instances to display.
        data_url: htmx fragment URL for all grid interactions.
        grid_id: HTML id for the grid container.
        exclude: Field names to exclude from display.
        include: Field names to include (if set, only these are shown).
        sort_field: Currently sorted field name.
        sort_order: Current sort order ("asc" or "desc").
        filters: Dict of field_name → ColumnFilter for filterable columns.
        filter_values: Current filter values (e.g. {"f_name": "alice"}).
        bulk_actions: List of (label, action_url) tuples for bulk operations.
        id_field: Field name used as row identifier for bulk actions.
        column_toggle: Enable column visibility toggling.
        visible_columns: List of currently visible column names (None = all).
        cell_renderers: Dict of field_name → callable(value) for custom cell rendering.
        extra_columns: Dict of column_name → callable(row) for additional columns.
        page: Current page number (1-indexed).
        total_pages: Total number of pages.
        total_items: Total number of items across all pages.
        per_page: Number of items per page.
        csv_url: URL for CSV export button (None = no export).
        zebra: Use zebra striping on table rows.
        compact: Use compact table size.
    """

    tag = "div"

    def __init__(
        self,
        model: type[BaseModel],
        rows: list[BaseModel],
        *,
        data_url: str,
        grid_id: str = "datagrid",
        exclude: list[str] | None = None,
        include: list[str] | None = None,
        sort_field: str | None = None,
        sort_order: str = "asc",
        filters: dict[str, ColumnFilter] | None = None,
        filter_values: dict[str, str] | None = None,
        bulk_actions: list[tuple[str, str]] | None = None,
        id_field: str = "id",
        column_toggle: bool = False,
        visible_columns: list[str] | None = None,
        cell_renderers: dict[str, Callable] | None = None,
        extra_columns: dict[str, Callable] | None = None,
        page: int = 1,
        total_pages: int = 1,
        total_items: int = 0,
        per_page: int = 20,
        csv_url: str | None = None,
        zebra: bool = True,
        compact: bool = False,
        **attrs: Any,
    ) -> None:
        self._model = model
        self._rows = rows
        self._data_url = data_url
        self._grid_id = grid_id
        self._sort_field = sort_field
        self._sort_order = sort_order if sort_order in ("asc", "desc") else "asc"
        self._filters = filters or {}
        self._filter_values = filter_values or {}
        self._bulk_actions = bulk_actions or []
        self._id_field = id_field
        self._column_toggle = column_toggle
        self._cell_renderers = cell_renderers or {}
        self._extra_columns = extra_columns or {}
        self._page = page
        self._total_pages = total_pages
        self._total_items = total_items
        self._per_page = per_page
        self._csv_url = csv_url
        self._zebra = zebra
        self._compact = compact

        # Get all model fields
        all_fields = _filter_fields(model, include, exclude)
        all_field_names = [name for name, _ in all_fields]

        # Apply visible_columns filter
        if visible_columns is not None:
            self._visible_columns = [c for c in visible_columns if c in all_field_names]
            if not self._visible_columns:
                self._visible_columns = all_field_names
        else:
            self._visible_columns = all_field_names

        self._all_field_names = all_field_names
        self._all_fields = all_fields

        # Visible fields for rendering
        visible_fields = [(n, fi) for n, fi in all_fields if n in self._visible_columns]

        has_checkbox = bool(self._bulk_actions)

        # Build grid children
        children: list[Any] = []
        children.append(self._build_hidden_state())

        toolbar = self._build_toolbar()
        if toolbar is not None:
            children.append(toolbar)

        # Table
        table_cls_parts = ["table"]
        if self._zebra:
            table_cls_parts.append("table-zebra")
        if self._compact:
            table_cls_parts.append("table-xs")
        table_cls = " ".join(table_cls_parts)

        thead_rows: list[Any] = [self._build_header_row(visible_fields, has_checkbox)]
        if self._filters:
            filter_row = self._build_filter_row(visible_fields, has_checkbox)
            if filter_row is not None:
                thead_rows.append(filter_row)

        table = Table(
            Thead(*thead_rows),
            Tbody(*self._build_body_rows(visible_fields, has_checkbox)),
            cls=table_cls,
        )
        children.append(Div(table, cls="overflow-x-auto"))

        children.append(self._build_footer())

        attrs["id"] = grid_id
        super().__init__(*children, **attrs)

    def _build_query_params(
        self,
        *,
        sort: str | None = None,
        order: str | None = None,
        page: int | None = None,
        toggle_column: str | None = None,
    ) -> list[tuple[str, str]]:
        """Build query parameter list with optional overrides."""
        params: list[tuple[str, str]] = []

        # Sort
        s = sort if sort is not None else self._sort_field
        o = order if order is not None else self._sort_order
        if s:
            params.append(("sort", s))
            params.append(("order", o))

        # Page
        p = page if page is not None else self._page
        params.append(("page", str(p)))

        # Filters
        for key, val in sorted(self._filter_values.items()):
            if val:
                params.append((key, val))

        # Columns
        if toggle_column is not None:
            cols = list(self._visible_columns)
            if toggle_column in cols:
                cols.remove(toggle_column)
            else:
                cols.append(toggle_column)
            if not cols:
                cols = list(self._all_field_names)
        else:
            cols = self._visible_columns if self._visible_columns != self._all_field_names else None

        if cols is not None and cols != self._all_field_names:
            for c in cols:
                params.append(("col", c))

        return params

    def _build_url(self, **overrides: Any) -> str:
        """Build a full URL with query string."""
        params = self._build_query_params(**overrides)
        if params:
            return f"{self._data_url}?{urlencode(params)}"
        return self._data_url

    def _build_hidden_state(self) -> Component:
        """Build hidden div with sort/order/col inputs for hx-include."""
        inputs: list[Any] = []
        if self._sort_field:
            inputs.append(Input(type="hidden", name="sort", value=self._sort_field))
            inputs.append(Input(type="hidden", name="order", value=self._sort_order))

        if self._visible_columns != self._all_field_names:
            for col in self._visible_columns:
                inputs.append(Input(type="hidden", name="col", value=col))

        return Div(*inputs, id=f"{self._grid_id}-state", style="display:none")

    def _build_toolbar(self) -> Component | None:
        """Build the toolbar with bulk actions dropdown, column toggle, and CSV export."""
        left_items: list[Any] = []
        right_items: list[Any] = []

        # Bulk actions dropdown
        if self._bulk_actions:
            action_items: list[Any] = []
            for label, action_url in self._bulk_actions:
                action_items.append(
                    Li(
                        A(
                            label,
                            hx_post=action_url,
                            hx_include=f"#{self._grid_id} [name=selected]",
                            hx_target=f"#{self._grid_id}",
                            hx_confirm=f"Are you sure you want to {label.lower()}?",
                        )
                    )
                )
            left_items.append(
                Div(
                    Div("Actions", tabindex="0", role="button", cls="btn btn-sm"),
                    Ul(
                        *action_items,
                        tabindex="0",
                        cls="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow",
                    ),
                    cls="dropdown",
                )
            )

        # Column toggle dropdown
        if self._column_toggle:
            col_items: list[Any] = []
            for col_name in self._all_field_names:
                is_visible = col_name in self._visible_columns
                label_text = f"\u2713 {col_name}" if is_visible else f"  {col_name}"
                toggle_url = self._build_url(toggle_column=col_name, page=1)
                col_items.append(
                    Li(
                        A(
                            label_text,
                            hx_get=toggle_url,
                            hx_target=f"#{self._grid_id}",
                        )
                    )
                )
            right_items.append(
                Div(
                    Div("Columns", tabindex="0", role="button", cls="btn btn-sm btn-outline"),
                    Ul(
                        *col_items,
                        tabindex="0",
                        cls="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow",
                    ),
                    cls="dropdown dropdown-end",
                )
            )

        # CSV export
        if self._csv_url:
            right_items.append(
                A("CSV", href=self._csv_url, cls="btn btn-sm btn-outline")
            )

        if not left_items and not right_items:
            return None

        return Div(
            Div(*left_items, cls="flex gap-2"),
            Div(*right_items, cls="flex gap-2"),
            cls="flex items-center justify-between mb-4",
        )

    def _build_header_row(
        self, fields: list[tuple[str, Any]], has_checkbox: bool
    ) -> Component:
        """Build the header row with sort links."""
        cells: list[Any] = []

        if has_checkbox:
            select_all_js = (
                "this.closest('table').querySelectorAll('input[name=selected]')"
                ".forEach(c=>c.checked=this.checked)"
            )
            cells.append(
                Th(Input(type="checkbox", cls="checkbox checkbox-sm", onclick=select_all_js))
            )

        for name, fi in fields:
            label = fi.title or name.replace("_", " ").title()
            if self._sort_field == name:
                indicator = " \u2191" if self._sort_order == "asc" else " \u2193"
                next_order = "desc" if self._sort_order == "asc" else "asc"
            else:
                indicator = ""
                next_order = "asc"
            sort_url = self._build_url(sort=name, order=next_order, page=1)
            link = A(
                f"{label}{indicator}",
                hx_get=sort_url,
                hx_target=f"#{self._grid_id}",
                style="cursor:pointer",
            )
            cells.append(Th(link))

        for col_name in self._extra_columns:
            cells.append(Th(col_name))

        return Tr(*cells)

    def _build_filter_row(
        self, fields: list[tuple[str, Any]], has_checkbox: bool
    ) -> Component | None:
        """Build the filter row with filter inputs."""
        if not self._filters:
            return None

        cells: list[Any] = []
        if has_checkbox:
            cells.append(Td())

        filter_id = f"{self._grid_id}-filters"
        state_id = f"{self._grid_id}-state"
        hx_include = f"#{filter_id} input, #{filter_id} select, #{state_id} input"

        has_any_filter = False
        for name, _fi in fields:
            if name not in self._filters:
                cells.append(Td())
                continue

            has_any_filter = True
            col_filter = self._filters[name]
            current_value = self._filter_values.get(f"f_{name}", "")

            common_attrs: dict[str, Any] = {
                "hx_get": self._data_url,
                "hx_target": f"#{self._grid_id}",
                "hx_include": hx_include,
                "hx_vals": '{"page": "1"}',
            }

            if col_filter.type == "text":
                cells.append(
                    Td(
                        Input(
                            type="text",
                            name=f"f_{name}",
                            value=current_value,
                            placeholder=col_filter.placeholder or name,
                            cls="input input-bordered input-sm w-full",
                            hx_trigger="keyup changed delay:300ms",
                            **common_attrs,
                        )
                    )
                )
            elif col_filter.type == "select":
                options: list[Any] = [Option("All", value="")]
                if col_filter.options:
                    for opt_val, opt_label in col_filter.options:
                        opt_attrs: dict[str, Any] = {"value": opt_val}
                        if current_value == opt_val:
                            opt_attrs["selected"] = True
                        options.append(Option(opt_label, **opt_attrs))
                cells.append(
                    Td(
                        Select(
                            *options,
                            name=f"f_{name}",
                            cls="select select-bordered select-sm w-full",
                            hx_trigger="change",
                            **common_attrs,
                        )
                    )
                )
            elif col_filter.type == "number_range":
                min_val = self._filter_values.get(f"f_{name}_min", "")
                max_val = self._filter_values.get(f"f_{name}_max", "")
                cells.append(
                    Td(
                        Div(
                            Input(
                                type="number",
                                name=f"f_{name}_min",
                                value=min_val,
                                placeholder="Min",
                                cls="input input-bordered input-sm w-20",
                                hx_trigger="change",
                                **common_attrs,
                            ),
                            Input(
                                type="number",
                                name=f"f_{name}_max",
                                value=max_val,
                                placeholder="Max",
                                cls="input input-bordered input-sm w-20",
                                hx_trigger="change",
                                **common_attrs,
                            ),
                            cls="flex gap-1",
                        )
                    )
                )
            else:
                cells.append(Td())

        # Add empty cells for extra columns
        for _ in self._extra_columns:
            cells.append(Td())

        if not has_any_filter:
            return None

        return Tr(*cells, id=filter_id)

    def _build_body_rows(
        self, fields: list[tuple[str, Any]], has_checkbox: bool
    ) -> list[Component]:
        """Build body rows for visible data."""
        rows: list[Component] = []
        for row in self._rows:
            cells: list[Any] = []

            if has_checkbox:
                row_id = getattr(row, self._id_field, "")
                cells.append(
                    Td(Input(type="checkbox", name="selected", value=str(row_id), cls="checkbox checkbox-sm"))
                )

            for name, _fi in fields:
                value = getattr(row, name)
                if name in self._cell_renderers:
                    cells.append(Td(self._cell_renderers[name](value)))
                else:
                    cells.append(Td(_render_value(value)))

            for renderer in self._extra_columns.values():
                cells.append(Td(renderer(row)))

            rows.append(Tr(*cells))
        return rows

    def _build_footer(self) -> Component:
        """Build footer with item count and pagination."""
        # Item count
        if self._total_items > 0:
            start = (self._page - 1) * self._per_page + 1
            end = min(self._page * self._per_page, self._total_items)
            count_text = f"Showing {start}-{end} of {self._total_items}"
        else:
            count_text = "No items"

        # Pagination
        page_buttons: list[Any] = []
        if self._total_pages > 1:
            # Previous
            if self._page > 1:
                page_buttons.append(
                    A(
                        "\u00ab",
                        hx_get=self._build_url(page=self._page - 1),
                        hx_target=f"#{self._grid_id}",
                        cls="join-item btn btn-sm",
                    )
                )
            else:
                page_buttons.append(
                    Button("\u00ab", cls="join-item btn btn-sm btn-disabled", disabled=True)
                )

            # Page numbers
            for p in range(1, self._total_pages + 1):
                if p == self._page:
                    page_buttons.append(
                        Button(str(p), cls="join-item btn btn-sm btn-active")
                    )
                else:
                    page_buttons.append(
                        A(
                            str(p),
                            hx_get=self._build_url(page=p),
                            hx_target=f"#{self._grid_id}",
                            cls="join-item btn btn-sm",
                        )
                    )

            # Next
            if self._page < self._total_pages:
                page_buttons.append(
                    A(
                        "\u00bb",
                        hx_get=self._build_url(page=self._page + 1),
                        hx_target=f"#{self._grid_id}",
                        cls="join-item btn btn-sm",
                    )
                )
            else:
                page_buttons.append(
                    Button("\u00bb", cls="join-item btn btn-sm btn-disabled", disabled=True)
                )

        pagination = Div(*page_buttons, cls="join") if page_buttons else Div()

        return Div(
            Span(count_text),
            pagination,
            cls="flex items-center justify-between mt-4",
        )
