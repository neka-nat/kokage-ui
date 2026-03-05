"""Tests for drag & drop sortable functionality."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from kokage_ui.data.crud import CRUDRouter, InMemoryStorage
from kokage_ui.fields.sortable import SortableList
from kokage_ui.page import Page, SORTABLEJS_CDN


# ========================================
# TestSortableList — component rendering
# ========================================


class TestSortableList:
    def test_renders_ul_with_items(self):
        sl = SortableList(
            items=[
                {"id": "1", "label": "First"},
                {"id": "2", "label": "Second"},
            ],
            url="/reorder",
            list_id="test-list",
        )
        html = sl.render()
        assert '<ul id="test-list"' in html
        assert 'data-id="1"' in html
        assert 'data-id="2"' in html
        assert "<span>First</span>" in html
        assert "<span>Second</span>" in html

    def test_renders_handle_by_default(self):
        sl = SortableList(
            items=[{"id": "1", "label": "Item"}],
            url="/reorder",
            list_id="test-list",
        )
        html = sl.render()
        assert "sortable-handle" in html
        assert "cursor-grab" in html
        assert "\u2807" in html

    def test_no_handle_when_disabled(self):
        sl = SortableList(
            items=[{"id": "1", "label": "Item"}],
            url="/reorder",
            handle=False,
            list_id="test-list",
        )
        html = sl.render()
        assert "sortable-handle" not in html

    def test_renders_badge(self):
        sl = SortableList(
            items=[{"id": "1", "label": "Item", "badge": "High"}],
            url="/reorder",
            list_id="test-list",
        )
        html = sl.render()
        assert "badge badge-ghost badge-sm" in html
        assert "High" in html

    def test_renders_script(self):
        sl = SortableList(
            items=[{"id": "1", "label": "Item"}],
            url="/api/reorder",
            list_id="test-list",
        )
        html = sl.render()
        assert "<script>" in html
        assert "Sortable.create" in html
        assert "/api/reorder" in html
        assert "typeof Sortable" in html

    def test_swap_none(self):
        sl = SortableList(
            items=[{"id": "1", "label": "Item"}],
            url="/reorder",
            list_id="test-list",
        )
        html = sl.render()
        assert "swap:'none'" in html

    def test_xss_protection(self):
        sl = SortableList(
            items=[{"id": '<script>alert("xss")</script>', "label": "<b>bad</b>"}],
            url="/reorder",
            list_id="test-list",
        )
        html = sl.render()
        assert "<script>alert" not in html
        assert "<b>bad</b>" not in html
        assert "&lt;" in html

    def test_group_option(self):
        sl = SortableList(
            items=[{"id": "1", "label": "Item"}],
            url="/reorder",
            group="shared",
            list_id="test-list",
        )
        html = sl.render()
        assert 'group:"shared"' in html

    def test_auto_generated_list_id(self):
        sl = SortableList(
            items=[{"id": "1", "label": "Item"}],
            url="/reorder",
        )
        html = sl.render()
        assert "kokage-sortable-" in html


# ========================================
# TestInMemoryStorageReorder
# ========================================


class Item(BaseModel):
    id: str = ""
    name: str = ""


class TestInMemoryStorageReorder:
    @pytest.mark.asyncio
    async def test_reorder(self):
        storage = InMemoryStorage(
            Item,
            initial=[
                Item(id="a", name="Alpha"),
                Item(id="b", name="Beta"),
                Item(id="c", name="Charlie"),
            ],
        )
        await storage.reorder(["c", "a", "b"])
        items, _ = await storage.list(skip=0, limit=10)
        ids = [item.id for item in items]
        assert ids == ["c", "a", "b"]

    @pytest.mark.asyncio
    async def test_reorder_partial_ids(self):
        storage = InMemoryStorage(
            Item,
            initial=[
                Item(id="a", name="Alpha"),
                Item(id="b", name="Beta"),
                Item(id="c", name="Charlie"),
            ],
        )
        # Only reorder a subset; missing items appended at end
        await storage.reorder(["c"])
        items, _ = await storage.list(skip=0, limit=10)
        ids = [item.id for item in items]
        assert ids == ["c", "a", "b"]

    @pytest.mark.asyncio
    async def test_reorder_empty_list(self):
        storage = InMemoryStorage(
            Item,
            initial=[Item(id="a", name="Alpha"), Item(id="b", name="Beta")],
        )
        await storage.reorder([])
        items, _ = await storage.list(skip=0, limit=10)
        ids = [item.id for item in items]
        assert ids == ["a", "b"]

    @pytest.mark.asyncio
    async def test_reorder_unknown_ids(self):
        storage = InMemoryStorage(
            Item,
            initial=[Item(id="a", name="Alpha")],
        )
        await storage.reorder(["x", "a", "y"])
        items, _ = await storage.list(skip=0, limit=10)
        ids = [item.id for item in items]
        assert ids == ["a"]


# ========================================
# TestCRUDRouterSortable
# ========================================


class Task(BaseModel):
    id: str = ""
    title: str = ""


class TestCRUDRouterSortable:
    @pytest.fixture
    def app_with_sortable(self):
        app = FastAPI()
        storage = InMemoryStorage(
            Task,
            initial=[
                Task(id="1", title="First"),
                Task(id="2", title="Second"),
                Task(id="3", title="Third"),
            ],
        )
        CRUDRouter(app, "/tasks", Task, storage, sortable=True)
        return app, storage

    @pytest.mark.asyncio
    async def test_reorder_route_exists(self, app_with_sortable):
        app, _ = app_with_sortable
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/tasks/_reorder",
                data={"ids": json.dumps(["3", "1", "2"])},
            )
            assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_reorder_updates_order(self, app_with_sortable):
        app, storage = app_with_sortable
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post(
                "/tasks/_reorder",
                data={"ids": json.dumps(["3", "1", "2"])},
            )
        items, _ = await storage.list(skip=0, limit=10)
        ids = [item.id for item in items]
        assert ids == ["3", "1", "2"]

    @pytest.mark.asyncio
    async def test_reorder_invalid_json_returns_400(self, app_with_sortable):
        app, _ = app_with_sortable
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/tasks/_reorder",
                data={"ids": "not-json"},
            )
            assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_list_page_includes_sortablejs_cdn(self, app_with_sortable):
        app, _ = app_with_sortable
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/tasks")
            assert SORTABLEJS_CDN in resp.text

    @pytest.mark.asyncio
    async def test_list_page_renders_sortable_list(self, app_with_sortable):
        app, _ = app_with_sortable
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/tasks")
            assert "Sortable.create" in resp.text
            assert "kokage-sortable-" in resp.text


# ========================================
# TestPageIncludeSortableJS
# ========================================


class TestPageIncludeSortableJS:
    def test_includes_sortablejs_when_enabled(self):
        page = Page(title="Test", include_sortablejs=True)
        html = page.render()
        assert SORTABLEJS_CDN in html

    def test_excludes_sortablejs_by_default(self):
        page = Page(title="Test")
        html = page.render()
        assert SORTABLEJS_CDN not in html
