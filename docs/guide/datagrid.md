# DataGrid

`DataGrid` is an advanced table component with sorting, filtering, pagination, bulk actions, column toggling, and CSV export. It's powered by htmx for seamless interactions.

## Quick Start

```python
from fastapi import Request
from kokage_ui import DataGrid, DataGridState

@ui.fragment("/items/_list")
async def items_list(request: Request):
    state = DataGridState.from_request(request)
    skip = (state.page - 1) * 20
    items, total = await storage.list(skip=skip, limit=20, search=None)
    total_pages = max(1, -(-total // 20))

    return DataGrid(
        Item,
        items,
        data_url="/items/_list",
        sort_field=state.sort_field,
        sort_order=state.sort_order,
        page=state.page,
        total_pages=total_pages,
        total_items=total,
    )
```

## DataGrid Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | type[BaseModel] | Pydantic model class |
| `rows` | list[BaseModel] | Data rows to display |
| `data_url` | str | htmx endpoint for all interactions |
| `grid_id` | str | HTML id (default: `"datagrid"`) |
| `exclude` | list[str] \| None | Fields to exclude |
| `include` | list[str] \| None | Fields to include (whitelist) |
| `sort_field` | str \| None | Current sort field |
| `sort_order` | str | `"asc"` or `"desc"` (default: `"asc"`) |
| `filters` | dict[str, ColumnFilter] \| None | Per-column filters |
| `filter_values` | dict[str, str] \| None | Current filter values |
| `bulk_actions` | list[tuple[str, str]] \| None | `[(label, action_url), ...]` |
| `id_field` | str | Primary key field (default: `"id"`) |
| `column_toggle` | bool | Enable column visibility toggle |
| `visible_columns` | list[str] \| None | Currently visible columns |
| `cell_renderers` | dict[str, Callable] \| None | Custom cell renderers |
| `extra_columns` | dict[str, Callable] \| None | Additional columns `{name: (row) -> Component}` |
| `page` | int | Current page (default: 1) |
| `total_pages` | int | Total pages |
| `total_items` | int | Total item count |
| `per_page` | int | Items per page (default: 20) |
| `csv_url` | str \| None | CSV export endpoint URL |
| `zebra` | bool | Zebra-striped rows (default: `True`) |
| `compact` | bool | Compact table style (default: `False`) |

## DataGridState

Parse grid state from request query parameters:

```python
state = DataGridState.from_request(request)
# state.sort_field   → "name"
# state.sort_order   → "asc"
# state.page         → 2
# state.filter_values → {"f_name": "alice"}
# state.clean_filters → {"name": "alice"}  (without f_ prefix)
```

Query parameters: `sort=field`, `order=asc|desc`, `page=N`, `f_name=value` (filters), `col=field` (visible columns).

## ColumnFilter

Define per-column filter inputs:

```python
from kokage_ui import ColumnFilter

filters = {
    "name": ColumnFilter(type="text", placeholder="Filter name..."),
    "status": ColumnFilter(type="select", options=[("active", "Active"), ("inactive", "Inactive")]),
    "price": ColumnFilter(type="number_range"),
}
```

| Type | Description |
|------|-------------|
| `"text"` | Text input with debounced keyup |
| `"select"` | Dropdown with predefined options |
| `"number_range"` | Min/max number inputs |

## Custom Cell Renderers

```python
DataGrid(
    Item,
    items,
    data_url="/items/_list",
    cell_renderers={
        "id": lambda v: A(str(v), href=f"/items/{v}"),
        "price": lambda v: Span(f"${v:.2f}", cls="font-mono"),
    },
)
```

## Extra Columns

Add computed columns (e.g., action buttons):

```python
def render_actions(row):
    return Div(
        A("Edit", href=f"/items/{row.id}/edit", cls="btn btn-warning btn-xs"),
        ConfirmDelete("Delete", url=f"/items/{row.id}", cls="btn btn-error btn-xs"),
        cls="flex gap-1",
    )

DataGrid(
    Item,
    items,
    data_url="/items/_list",
    extra_columns={"Actions": render_actions},
)
```

## Bulk Actions

```python
DataGrid(
    Item,
    items,
    data_url="/items/_list",
    bulk_actions=[
        ("Delete Selected", "/items/_bulk_delete"),
        ("Export Selected", "/items/_export"),
    ],
)
```

Bulk action endpoints receive `selected` form values (list of IDs from checked rows).
