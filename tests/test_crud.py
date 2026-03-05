"""Tests for CRUD auto-generation."""

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from kokage_ui import InMemoryStorage, KokageUI, Page
from kokage_ui.crud import CRUDRouter, Pagination


# ---- Test models ----


class Item(BaseModel):
    id: str = ""
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    is_active: bool = True


def _make_items() -> list[Item]:
    return [
        Item(id="1", name="Widget", price=9.99, is_active=True),
        Item(id="2", name="Gadget", price=19.99, is_active=False),
        Item(id="3", name="Doohickey", price=4.50, is_active=True),
    ]


# ========================================
# InMemoryStorage tests
# ========================================


class TestInMemoryStorage:
    def test_list_all(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        items, total = asyncio.run(storage.list())
        assert total == 3
        assert len(items) == 3

    def test_list_pagination(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        items, total = asyncio.run(storage.list(skip=0, limit=2))
        assert len(items) == 2
        assert total == 3

    def test_list_pagination_offset(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        items, total = asyncio.run(storage.list(skip=2, limit=2))
        assert len(items) == 1
        assert total == 3

    def test_list_search(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        items, total = asyncio.run(storage.list(search="widget"))
        assert total == 1
        assert items[0].name == "Widget"

    def test_list_search_no_match(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        items, total = asyncio.run(storage.list(search="nonexistent"))
        assert total == 0
        assert len(items) == 0

    def test_get_existing(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        item = asyncio.run(storage.get("1"))
        assert item is not None
        assert item.name == "Widget"

    def test_get_nonexistent(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        item = asyncio.run(storage.get("999"))
        assert item is None

    def test_create(self):
        storage = InMemoryStorage(Item, initial=[])
        created = asyncio.run(storage.create(Item(name="New", price=5.0)))
        assert created.id != ""
        assert created.name == "New"
        # Verify persisted
        fetched = asyncio.run(storage.get(created.id))
        assert fetched is not None

    def test_create_with_id(self):
        storage = InMemoryStorage(Item, initial=[])
        created = asyncio.run(storage.create(Item(id="custom", name="New", price=5.0)))
        assert created.id == "custom"

    def test_update(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        updated = asyncio.run(
            storage.update("1", Item(name="Updated Widget", price=12.0))
        )
        assert updated is not None
        assert updated.name == "Updated Widget"
        assert updated.id == "1"

    def test_update_nonexistent(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        result = asyncio.run(
            storage.update("999", Item(name="Ghost", price=0))
        )
        assert result is None

    def test_delete(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        assert asyncio.run(storage.delete("1")) is True
        assert asyncio.run(storage.get("1")) is None

    def test_delete_nonexistent(self):
        storage = InMemoryStorage(Item, initial=_make_items())
        assert asyncio.run(storage.delete("999")) is False

    def test_auto_id_on_empty(self):
        storage = InMemoryStorage(Item, initial=[Item(name="NoID", price=1.0)])
        items, _ = asyncio.run(storage.list())
        assert items[0].id != ""


# ========================================
# Pagination tests
# ========================================


class TestPagination:
    def test_single_page_empty(self):
        p = Pagination(current_page=1, total_pages=1, base_url="/items/_list")
        html = str(p)
        # Should render empty div (no buttons)
        assert "join-item" not in html

    def test_multiple_pages(self):
        p = Pagination(current_page=1, total_pages=3, base_url="/items/_list")
        html = str(p)
        assert "1" in html
        assert "2" in html
        assert "3" in html
        assert "btn-active" in html

    def test_active_page(self):
        p = Pagination(current_page=2, total_pages=3, base_url="/items/_list")
        html = str(p)
        # Page 2 should be active
        assert "btn-active" in html

    def test_search_param_preserved(self):
        p = Pagination(
            current_page=1,
            total_pages=2,
            base_url="/items/_list",
            search="widget",
        )
        html = str(p)
        assert "q=widget" in html


# ========================================
# CRUD integration tests with FastAPI TestClient
# ========================================


@pytest.fixture
def crud_app():
    app = FastAPI()
    ui = KokageUI(app)
    storage = InMemoryStorage(Item, initial=_make_items())
    ui.crud("/items", model=Item, storage=storage, title="Items")
    return app


@pytest.fixture
def client(crud_app):
    return TestClient(crud_app)


class TestCRUDListPage:
    def test_list_page_returns_html(self, client):
        response = client.get("/items")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "Items" in response.text

    def test_list_page_has_new_link(self, client):
        response = client.get("/items")
        assert "/items/new" in response.text

    def test_list_page_has_search(self, client):
        response = client.get("/items")
        assert "Search" in response.text.lower() or "search" in response.text.lower()


class TestCRUDListFragment:
    def test_list_fragment(self, client):
        response = client.get("/items/_list")
        assert response.status_code == 200
        assert "Widget" in response.text
        assert "<!DOCTYPE html>" not in response.text

    def test_list_fragment_search(self, client):
        response = client.get("/items/_list?q=gadget")
        assert response.status_code == 200
        assert "Gadget" in response.text
        assert "Widget" not in response.text

    def test_list_fragment_pagination(self, client):
        # Create app with small per_page
        app = FastAPI()
        ui = KokageUI(app)
        storage = InMemoryStorage(Item, initial=_make_items())
        ui.crud("/items", model=Item, storage=storage, per_page=2)
        c = TestClient(app)

        response = c.get("/items/_list?page=1")
        assert response.status_code == 200
        # Should have pagination buttons
        assert "join-item" in response.text


class TestCRUDCreatePage:
    def test_create_page(self, client):
        response = client.get("/items/new")
        assert response.status_code == 200
        assert "<form" in response.text
        assert 'name="name"' in response.text

    def test_create_success(self, client):
        response = client.post(
            "/items/new",
            data={"name": "New Item", "price": "15.00"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/items/" in response.headers["location"]

    def test_create_htmx_success(self, client):
        response = client.post(
            "/items/new",
            data={"name": "New Item", "price": "15.00"},
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "HX-Redirect" in response.headers

    def test_create_validation_error(self, client):
        response = client.post(
            "/items/new",
            data={"name": "", "price": "-1"},
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "error" in response.text.lower() or "text-error" in response.text

    def test_create_validation_error_htmx(self, client):
        response = client.post(
            "/items/new",
            data={"name": "", "price": "-1"},
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "<form" in response.text


class TestCRUDDetailPage:
    def test_detail_page(self, client):
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "Widget" in response.text

    def test_detail_page_has_edit_link(self, client):
        response = client.get("/items/1")
        assert "/items/1/edit" in response.text

    def test_detail_page_has_delete_button(self, client):
        response = client.get("/items/1")
        assert "Delete" in response.text

    def test_detail_not_found(self, client):
        response = client.get("/items/999")
        assert response.status_code == 404


class TestCRUDEditPage:
    def test_edit_page(self, client):
        response = client.get("/items/1/edit")
        assert response.status_code == 200
        assert "<form" in response.text
        # Should have pre-filled value
        assert "Widget" in response.text

    def test_edit_page_not_found(self, client):
        response = client.get("/items/999/edit")
        assert response.status_code == 404

    def test_edit_success(self, client):
        response = client.post(
            "/items/1/edit",
            data={"name": "Updated Widget", "price": "12.00"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"].startswith("/items/1")

    def test_edit_htmx_success(self, client):
        response = client.post(
            "/items/1/edit",
            data={"name": "Updated Widget", "price": "12.00"},
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert response.headers["HX-Redirect"].startswith("/items/1")

    def test_edit_validation_error(self, client):
        response = client.post(
            "/items/1/edit",
            data={"name": "", "price": "-1"},
            follow_redirects=False,
        )
        assert response.status_code == 422


class TestCRUDDelete:
    def test_delete_htmx(self, client):
        response = client.delete(
            "/items/1",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert response.headers["HX-Redirect"].startswith("/items")

    def test_delete_not_found(self, client):
        response = client.delete("/items/999")
        assert response.status_code == 404

    def test_delete_normal(self, client):
        response = client.delete("/items/1", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"].startswith("/items")


class TestCRUDPageWrapper:
    def test_page_wrapper_used(self):
        app = FastAPI()
        ui = KokageUI(app)
        storage = InMemoryStorage(Item, initial=_make_items())

        def my_wrapper(content, title):
            return Page(
                content,
                title=f"Custom: {title}",
            )

        ui.crud("/items", model=Item, storage=storage, page_wrapper=my_wrapper)
        c = TestClient(app)

        response = c.get("/items")
        assert response.status_code == 200
        assert "Custom:" in response.text


class TestCRUDBoolHandling:
    def test_bool_field_unchecked(self, client):
        """Bool field missing from form data should be treated as False."""
        response = client.post(
            "/items/new",
            data={"name": "No Active", "price": "5.00"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        # Item was created; verify by checking the list
        list_response = client.get("/items/_list")
        assert "No Active" in list_response.text


class TestCRUDActionColumn:
    def test_list_has_edit_links(self, client):
        response = client.get("/items/_list")
        assert "/items/1/edit" in response.text
        assert "Edit" in response.text

    def test_list_has_delete_buttons(self, client):
        response = client.get("/items/_list")
        assert "Delete" in response.text
        assert "hx-delete" in response.text

    def test_actions_header(self, client):
        response = client.get("/items/_list")
        assert "<th>Actions</th>" in response.text


class TestCRUDToast:
    def test_create_toast_param(self, client):
        response = client.post(
            "/items/new",
            data={"name": "New Item", "price": "15.00"},
            follow_redirects=False,
        )
        assert "_toast=" in response.headers["location"]

    def test_edit_toast_param(self, client):
        response = client.post(
            "/items/1/edit",
            data={"name": "Updated Widget", "price": "12.00"},
            follow_redirects=False,
        )
        assert "_toast=" in response.headers["location"]

    def test_delete_toast_param(self, client):
        response = client.delete("/items/1", follow_redirects=False)
        assert "_toast=" in response.headers["location"]

    def test_default_page_includes_toast(self, client):
        """Default _wrap_page (no page_wrapper) includes toast support."""
        response = client.get("/items")
        assert "kokage-toast" in response.text
