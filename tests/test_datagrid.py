"""Tests for the DataGrid component."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from kokage_ui.data.datagrid import ColumnFilter, DataGrid, DataGridState


# ========================================
# Test models
# ========================================


class Item(BaseModel):
    id: int
    name: str
    status: str
    price: float


class SimpleModel(BaseModel):
    id: int
    title: str


def _make_items(n: int = 3) -> list[Item]:
    return [
        Item(id=i, name=f"Item {i}", status="active" if i % 2 == 0 else "inactive", price=10.0 * i)
        for i in range(1, n + 1)
    ]


def _make_request(params: dict[str, str | list[str]] | None = None) -> MagicMock:
    """Create a mock Starlette Request with query_params."""
    mock = MagicMock()

    class FakeQueryParams:
        def __init__(self, params: dict[str, str | list[str]] | None):
            self._params = params or {}

        def get(self, key: str, default: str | None = None) -> str | None:
            val = self._params.get(key, default)
            if isinstance(val, list):
                return val[0] if val else default
            return val

        def getlist(self, key: str) -> list[str]:
            val = self._params.get(key)
            if val is None:
                return []
            if isinstance(val, list):
                return val
            return [val]

        def __iter__(self):
            return iter(self._params)

        def __getitem__(self, key: str) -> str:
            val = self._params[key]
            if isinstance(val, list):
                return val[0]
            return val

    mock.query_params = FakeQueryParams(params)
    return mock


# ========================================
# TestColumnFilter
# ========================================


class TestColumnFilter:
    def test_default_values(self):
        f = ColumnFilter()
        assert f.type == "text"
        assert f.options is None
        assert f.placeholder == ""

    def test_custom_values(self):
        f = ColumnFilter(type="number_range", placeholder="Search...")
        assert f.type == "number_range"
        assert f.placeholder == "Search..."

    def test_select_with_options(self):
        f = ColumnFilter(type="select", options=[("a", "Active"), ("i", "Inactive")])
        assert f.type == "select"
        assert f.options == [("a", "Active"), ("i", "Inactive")]


# ========================================
# TestDataGridState
# ========================================


class TestDataGridState:
    def test_from_request_full(self):
        req = _make_request({
            "sort": "name",
            "order": "desc",
            "page": "3",
            "f_name": "alice",
            "f_status": "active",
            "col": ["name", "status"],
        })
        state = DataGridState.from_request(req)
        assert state.sort_field == "name"
        assert state.sort_order == "desc"
        assert state.page == 3
        assert state.filter_values == {"f_name": "alice", "f_status": "active"}
        assert state.visible_columns == ["name", "status"]

    def test_from_request_empty(self):
        req = _make_request({})
        state = DataGridState.from_request(req)
        assert state.sort_field is None
        assert state.sort_order == "asc"
        assert state.page == 1
        assert state.filter_values == {}
        assert state.visible_columns is None

    def test_from_request_filters_only(self):
        req = _make_request({"f_name": "bob"})
        state = DataGridState.from_request(req)
        assert state.filter_values == {"f_name": "bob"}
        assert state.sort_field is None

    def test_from_request_cols_only(self):
        req = _make_request({"col": ["id", "name"]})
        state = DataGridState.from_request(req)
        assert state.visible_columns == ["id", "name"]

    def test_from_request_invalid_page(self):
        req = _make_request({"page": "abc"})
        state = DataGridState.from_request(req)
        assert state.page == 1

    def test_from_request_negative_page(self):
        req = _make_request({"page": "-5"})
        state = DataGridState.from_request(req)
        assert state.page == 1

    def test_from_request_invalid_order(self):
        req = _make_request({"order": "invalid"})
        state = DataGridState.from_request(req)
        assert state.sort_order == "asc"

    def test_clean_filters(self):
        state = DataGridState(
            filter_values={"f_name": "alice", "f_status": "active", "f_empty": ""}
        )
        assert state.clean_filters == {"name": "alice", "status": "active"}

    def test_clean_filters_empty(self):
        state = DataGridState()
        assert state.clean_filters == {}


# ========================================
# TestDataGrid
# ========================================


class TestDataGrid:
    def test_basic_render(self):
        items = _make_items(2)
        html = str(DataGrid(Item, items, data_url="/grid"))
        assert 'id="datagrid"' in html
        assert "<table" in html
        assert "Item 1" in html
        assert "Item 2" in html

    def test_sort_headers(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid"))
        # All field headers should be links
        assert "Id" in html
        assert "Name" in html
        assert "Status" in html
        assert "Price" in html
        # Sort links should have hx-get with sort params
        assert "sort=id" in html
        assert "sort=name" in html

    def test_sort_arrows(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", sort_field="name", sort_order="asc"))
        assert "Name \u2191" in html
        # Sorted column should link to opposite order
        assert "order=desc" in html

    def test_sort_arrows_desc(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", sort_field="name", sort_order="desc"))
        assert "Name \u2193" in html
        assert "order=asc" in html

    def test_filter_row_text(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            filters={"name": ColumnFilter()},
        ))
        assert 'name="f_name"' in html
        assert "keyup changed delay:300ms" in html

    def test_filter_row_select(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            filters={"status": ColumnFilter(type="select", options=[("active", "Active"), ("inactive", "Inactive")])},
        ))
        assert 'name="f_status"' in html
        assert "<select" in html
        assert "Active" in html
        assert "Inactive" in html
        assert "All" in html

    def test_filter_row_number_range(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            filters={"price": ColumnFilter(type="number_range")},
        ))
        assert 'name="f_price_min"' in html
        assert 'name="f_price_max"' in html
        assert 'type="number"' in html

    def test_filter_preserves_values(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            filters={"name": ColumnFilter()},
            filter_values={"f_name": "test"},
        ))
        assert 'value="test"' in html

    def test_select_filter_preserves_selected(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            filters={"status": ColumnFilter(type="select", options=[("active", "Active"), ("inactive", "Inactive")])},
            filter_values={"f_status": "active"},
        ))
        assert "selected" in html

    def test_bulk_checkboxes(self):
        items = _make_items(2)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            bulk_actions=[("Delete", "/delete")],
        ))
        assert 'name="selected"' in html
        assert 'value="1"' in html
        assert 'value="2"' in html

    def test_bulk_actions_dropdown(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            bulk_actions=[("Delete", "/delete"), ("Archive", "/archive")],
        ))
        assert "Actions" in html
        assert "Delete" in html
        assert "Archive" in html
        assert 'hx-post="/delete"' in html
        assert 'hx-post="/archive"' in html

    def test_select_all_checkbox(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            bulk_actions=[("Delete", "/delete")],
        ))
        assert "forEach" in html
        assert "checked=this.checked" in html

    def test_column_toggle(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            column_toggle=True,
        ))
        assert "Columns" in html
        # All columns should appear in toggle dropdown with checkmarks
        assert "\u2713 id" in html
        assert "\u2713 name" in html

    def test_csv_button(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            csv_url="/export.csv",
        ))
        assert "CSV" in html
        assert 'href="/export.csv"' in html

    def test_pagination(self):
        items = _make_items(2)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            page=2,
            total_pages=5,
            total_items=100,
            per_page=20,
        ))
        # Page buttons
        assert "1" in html
        assert "2" in html
        assert "5" in html
        # Previous and next
        assert "\u00ab" in html
        assert "\u00bb" in html

    def test_pagination_first_page(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            page=1,
            total_pages=3,
            total_items=60,
        ))
        # Previous should be disabled
        assert "btn-disabled" in html

    def test_pagination_last_page(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            page=3,
            total_pages=3,
            total_items=60,
        ))
        # Next button should be disabled (appears as btn-disabled)
        assert "btn-disabled" in html

    def test_pagination_single_page(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            page=1,
            total_pages=1,
            total_items=1,
        ))
        # No pagination join div content
        assert "join-item" not in html

    def test_footer_item_count(self):
        items = _make_items(2)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            page=2,
            total_pages=5,
            total_items=100,
            per_page=20,
        ))
        assert "Showing 21-40 of 100" in html

    def test_footer_no_items(self):
        html = str(DataGrid(
            Item, [],
            data_url="/grid",
            total_items=0,
        ))
        assert "No items" in html

    def test_cell_renderers(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            cell_renderers={"name": lambda v: f"**{v}**"},
        ))
        assert "**Item 1**" in html

    def test_extra_columns(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            extra_columns={"Actions": lambda row: f"Edit {row.id}"},
        ))
        assert "Actions" in html
        assert "Edit 1" in html

    def test_visible_columns(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            visible_columns=["id", "name"],
        ))
        # Visible columns should be shown
        assert "Id" in html
        assert "Name" in html
        # Hidden column header should not be in the table headers
        # (but price value "10.0" won't appear in cells)
        assert "10.0" not in html

    def test_visible_columns_invalid_fallback(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            visible_columns=["nonexistent"],
        ))
        # Should fall back to all columns
        assert "Id" in html
        assert "Name" in html

    def test_zebra(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", zebra=True))
        assert "table-zebra" in html

    def test_no_zebra(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", zebra=False))
        assert "table-zebra" not in html

    def test_compact(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", compact=True))
        assert "table-xs" in html

    def test_hidden_state(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            sort_field="name",
            sort_order="desc",
        ))
        assert 'id="datagrid-state"' in html
        assert 'name="sort"' in html
        assert 'value="name"' in html
        assert 'name="order"' in html
        assert 'value="desc"' in html

    def test_empty_rows(self):
        html = str(DataGrid(Item, [], data_url="/grid"))
        assert "<table" in html
        assert "No items" in html

    def test_custom_grid_id(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", grid_id="my-grid"))
        assert 'id="my-grid"' in html
        assert 'id="my-grid-state"' in html

    def test_exclude_fields(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", exclude=["price", "status"]))
        assert "Price" not in html
        assert "Status" not in html
        assert "Name" in html

    def test_include_fields(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid", include=["id", "name"]))
        assert "Id" in html
        assert "Name" in html
        assert "Price" not in html

    def test_no_toolbar_when_empty(self):
        items = _make_items(1)
        html = str(DataGrid(Item, items, data_url="/grid"))
        # No bulk actions, no column toggle, no CSV → no toolbar
        assert "Actions" not in html
        assert "Columns" not in html
        assert "CSV" not in html

    def test_filter_row_not_rendered_when_no_filters(self):
        items = _make_items(1)
        grid = DataGrid(Item, items, data_url="/grid")
        html = str(grid)
        assert "datagrid-filters" not in html

    def test_hx_include_on_filters(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            filters={"name": ColumnFilter()},
        ))
        assert "#datagrid-filters" in html
        assert "#datagrid-state" in html

    def test_filter_hx_vals_page_reset(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            filters={"name": ColumnFilter()},
        ))
        # Value is HTML-escaped by markupsafe
        assert "page" in html
        assert 'hx-vals' in html

    def test_bulk_action_hx_include_selected(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            bulk_actions=[("Delete", "/delete")],
        ))
        assert "[name=selected]" in html

    def test_column_toggle_hidden_columns(self):
        items = _make_items(1)
        html = str(DataGrid(
            Item, items,
            data_url="/grid",
            column_toggle=True,
            visible_columns=["id", "name"],
        ))
        assert "\u2713 id" in html
        assert "\u2713 name" in html
        # Hidden columns should show without checkmark
        assert "  status" in html
        assert "  price" in html


# ========================================
# TestDataGridIntegration
# ========================================


class TestDataGridIntegration:
    """Integration tests using FastAPI TestClient."""

    def test_filter_round_trip(self):
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import HTMLResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        async def grid(request: Request) -> HTMLResponse:
            state = DataGridState.from_request(request)
            items = _make_items(3)
            clean = state.clean_filters
            if "name" in clean:
                items = [i for i in items if clean["name"].lower() in i.name.lower()]
            return HTMLResponse(str(DataGrid(
                Item, items,
                data_url="/grid",
                filters={"name": ColumnFilter()},
                filter_values=state.filter_values,
                sort_field=state.sort_field,
                sort_order=state.sort_order,
                page=state.page,
            )))

        app = Starlette(routes=[Route("/grid", grid)])
        client = TestClient(app)

        # No filter
        resp = client.get("/grid")
        assert resp.status_code == 200
        assert "Item 1" in resp.text
        assert "Item 2" in resp.text
        assert "Item 3" in resp.text

        # With filter
        resp = client.get("/grid?f_name=Item 2")
        assert resp.status_code == 200
        assert "Item 2" in resp.text
        assert "Item 1" not in resp.text
        assert "Item 3" not in resp.text

    def test_sort_round_trip(self):
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import HTMLResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        async def grid(request: Request) -> HTMLResponse:
            state = DataGridState.from_request(request)
            items = _make_items(3)
            if state.sort_field == "name":
                items.sort(key=lambda x: x.name, reverse=(state.sort_order == "desc"))
            return HTMLResponse(str(DataGrid(
                Item, items,
                data_url="/grid",
                sort_field=state.sort_field,
                sort_order=state.sort_order,
            )))

        app = Starlette(routes=[Route("/grid", grid)])
        client = TestClient(app)

        # Sort by name desc
        resp = client.get("/grid?sort=name&order=desc")
        assert resp.status_code == 200
        text = resp.text
        # Item 3 should appear before Item 1
        pos3 = text.index("Item 3")
        pos1 = text.index("Item 1")
        assert pos3 < pos1

    def test_bulk_action_round_trip(self):
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import HTMLResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        deleted_ids: list[str] = []

        async def grid(request: Request) -> HTMLResponse:
            items = _make_items(3)
            return HTMLResponse(str(DataGrid(
                Item, items,
                data_url="/grid",
                bulk_actions=[("Delete", "/bulk/delete")],
            )))

        async def bulk_delete(request: Request) -> HTMLResponse:
            form = await request.form()
            ids = form.getlist("selected")
            deleted_ids.extend(ids)
            return HTMLResponse("<div>Deleted</div>")

        app = Starlette(routes=[
            Route("/grid", grid),
            Route("/bulk/delete", bulk_delete, methods=["POST"]),
        ])
        client = TestClient(app)

        resp = client.post(
            "/bulk/delete",
            content="selected=1&selected=3",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        assert deleted_ids == ["1", "3"]
