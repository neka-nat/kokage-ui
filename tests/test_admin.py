"""Tests for admin dashboard generator."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from kokage_ui.data.crud import InMemoryStorage
from kokage_ui.features.admin import AdminSite, ModelAdmin


# ---- Test models ----


class User(BaseModel):
    id: str = ""
    name: str = Field(min_length=1)
    email: str = ""
    is_active: bool = True


class Product(BaseModel):
    id: str = ""
    name: str = Field(min_length=1)
    price: float = Field(ge=0)


def _make_users() -> list[User]:
    return [
        User(id="1", name="Alice", email="alice@example.com", is_active=True),
        User(id="2", name="Bob", email="bob@example.com", is_active=False),
        User(id="3", name="Charlie", email="charlie@example.com", is_active=True),
    ]


def _make_products() -> list[Product]:
    return [
        Product(id="p1", name="Widget", price=9.99),
        Product(id="p2", name="Gadget", price=19.99),
    ]


def _make_app(auth_check=None):
    """Create a test app with admin site and registered models."""
    app = FastAPI()
    user_storage = InMemoryStorage(User, initial=_make_users())
    product_storage = InMemoryStorage(Product, initial=_make_products())
    admin = AdminSite(app, prefix="/admin", title="Test Admin", auth_check=auth_check)
    admin.register(User, storage=user_storage)
    admin.register(Product, storage=product_storage, list_fields=["name", "price"])
    return app, admin, user_storage, product_storage


# ========================================
# TestModelAdmin
# ========================================


class TestModelAdmin:
    def test_defaults(self):
        storage = InMemoryStorage(User, initial=[])
        admin = ModelAdmin(model=User, storage=storage)
        assert admin.name == "user"
        assert admin.title == "Users"
        assert admin.icon == "U"
        assert admin.per_page == 20
        assert admin.id_field == "id"

    def test_auto_naming(self):
        storage = InMemoryStorage(Product, initial=[])
        admin = ModelAdmin(model=Product, storage=storage)
        assert admin.name == "product"
        assert admin.title == "Products"
        assert admin.icon == "P"

    def test_custom_values(self):
        storage = InMemoryStorage(User, initial=[])
        admin = ModelAdmin(
            model=User,
            storage=storage,
            name="members",
            title="Members",
            icon="M",
            per_page=10,
        )
        assert admin.name == "members"
        assert admin.title == "Members"
        assert admin.icon == "M"
        assert admin.per_page == 10

    def test_list_fields(self):
        storage = InMemoryStorage(User, initial=[])
        admin = ModelAdmin(
            model=User,
            storage=storage,
            list_fields=["name", "email"],
        )
        assert admin.list_fields == ["name", "email"]

    def test_form_exclude(self):
        storage = InMemoryStorage(User, initial=[])
        admin = ModelAdmin(
            model=User,
            storage=storage,
            form_exclude=["email"],
        )
        assert admin.form_exclude == ["email"]


# ========================================
# TestAdminSite
# ========================================


class TestAdminSite:
    def test_init(self):
        app = FastAPI()
        admin = AdminSite(app, prefix="/admin", title="My Admin")
        assert admin.prefix == "/admin"
        assert admin.title == "My Admin"
        assert admin.theme == "corporate"

    def test_register(self):
        app = FastAPI()
        admin = AdminSite(app, prefix="/admin")
        storage = InMemoryStorage(User, initial=[])
        admin.register(User, storage=storage)
        assert len(admin._registrations) == 1
        assert admin._registrations[0].name == "user"

    def test_route_count(self):
        app, admin, _, _ = _make_app()
        # Count routes registered by admin
        # Dashboard: 1 GET
        # Per model (2 models): 10 routes each = 20
        # Total: 21
        route_paths = [r.path for r in app.routes]
        admin_routes = [p for p in route_paths if p.startswith("/admin")]
        assert len(admin_routes) >= 21


# ========================================
# TestAdminDashboard
# ========================================


class TestAdminDashboard:
    def test_dashboard_returns_200(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/")
        assert resp.status_code == 200

    def test_dashboard_contains_model_titles(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/")
        assert "Users" in resp.text
        assert "Products" in resp.text

    def test_dashboard_contains_counts(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/")
        # 3 users, 2 products
        assert "3" in resp.text
        assert "2" in resp.text

    def test_dashboard_contains_stats(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/")
        assert "stat-value" in resp.text

    def test_dashboard_contains_nav_links(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/")
        assert "/admin/user/" in resp.text
        assert "/admin/product/" in resp.text


# ========================================
# TestAdminListPage
# ========================================


class TestAdminListPage:
    def test_list_page_returns_200(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/")
        assert resp.status_code == 200

    def test_list_page_contains_datagrid(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/")
        assert "user-grid" in resp.text

    def test_list_page_contains_items(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/")
        assert "Alice" in resp.text
        assert "Bob" in resp.text


# ========================================
# TestAdminListFragment
# ========================================


class TestAdminListFragment:
    def test_list_fragment_returns_200(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/_list")
        assert resp.status_code == 200

    def test_list_fragment_is_partial(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/_list")
        # Fragment should not contain full HTML doc
        assert "<!DOCTYPE html>" not in resp.text
        # But should contain grid
        assert "user-grid" in resp.text


# ========================================
# TestAdminCreate
# ========================================


class TestAdminCreate:
    def test_create_form_page(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/new")
        assert resp.status_code == 200
        assert "New User" in resp.text
        assert "<form" in resp.text

    def test_create_valid_normal(self):
        app, _, user_storage, _ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/new",
            data={"name": "Dave", "email": "dave@example.com"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert "/admin/user/" in resp.headers["location"]

    def test_create_valid_htmx(self):
        app, _, user_storage, _ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/new",
            data={"name": "Eve", "email": "eve@example.com"},
            headers={"hx-request": "true"},
        )
        assert resp.status_code == 200
        assert "HX-Redirect" in resp.headers

    def test_create_invalid_normal(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/new",
            data={"name": "", "email": "bad"},
            follow_redirects=False,
        )
        assert resp.status_code == 422

    def test_create_invalid_htmx(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/new",
            data={"name": "", "email": "bad"},
            headers={"hx-request": "true"},
        )
        assert resp.status_code == 422
        # Should return form fragment with errors
        assert "text-error" in resp.text


# ========================================
# TestAdminDetail
# ========================================


class TestAdminDetail:
    def test_detail_page(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/1")
        assert resp.status_code == 200
        assert "Alice" in resp.text

    def test_detail_404(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/999")
        assert resp.status_code == 404

    def test_detail_has_actions(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/1")
        assert "Edit" in resp.text
        assert "Delete" in resp.text
        assert "Back to list" in resp.text


# ========================================
# TestAdminEdit
# ========================================


class TestAdminEdit:
    def test_edit_form_prefilled(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/1/edit")
        assert resp.status_code == 200
        assert "Alice" in resp.text
        assert "Edit User" in resp.text

    def test_edit_404(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/999/edit")
        assert resp.status_code == 404

    def test_edit_valid_normal(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/1/edit",
            data={"name": "Alice Updated", "email": "alice2@example.com"},
            follow_redirects=False,
        )
        assert resp.status_code == 303

    def test_edit_valid_htmx(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/1/edit",
            data={"name": "Alice Updated", "email": "alice2@example.com"},
            headers={"hx-request": "true"},
        )
        assert resp.status_code == 200
        assert "HX-Redirect" in resp.headers

    def test_edit_invalid(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/1/edit",
            data={"name": "", "email": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 422


# ========================================
# TestAdminDelete
# ========================================


class TestAdminDelete:
    def test_delete_htmx(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.delete(
            "/admin/user/1",
            headers={"hx-request": "true"},
        )
        assert resp.status_code == 200
        assert "HX-Redirect" in resp.headers

    def test_delete_normal(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.delete("/admin/user/1", follow_redirects=False)
        assert resp.status_code == 303

    def test_delete_404(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.delete("/admin/user/999")
        assert resp.status_code == 404


# ========================================
# TestAdminBulkDelete
# ========================================


class TestAdminBulkDelete:
    def test_bulk_delete(self):
        app, _, user_storage, _ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/user/_bulk_delete",
            data={"selected": ["1", "2"]},
        )
        assert resp.status_code == 200
        # Grid should re-render with remaining items
        assert "user-grid" in resp.text
        assert "Charlie" in resp.text


# ========================================
# TestAdminCSVExport
# ========================================


class TestAdminCSVExport:
    def test_csv_export(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/_csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]

    def test_csv_contains_headers(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/_csv")
        lines = resp.text.strip().split("\n")
        assert "id" in lines[0]
        assert "name" in lines[0]

    def test_csv_contains_data(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/user/_csv")
        assert "Alice" in resp.text
        assert "Bob" in resp.text

    def test_csv_respects_list_fields(self):
        """Product model is registered with list_fields=["name", "price"]."""
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/product/_csv")
        lines = resp.text.strip().split("\n")
        header = lines[0]
        assert "name" in header
        assert "price" in header
        # id should be excluded since list_fields doesn't include it
        assert header.split(",")[0] != "id"


# ========================================
# TestAdminAuth
# ========================================


class TestAdminAuth:
    def test_redirect_when_unauthenticated(self):
        def get_user(request):
            return None

        app, *_ = _make_app(auth_check=get_user)
        client = TestClient(app)
        resp = client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]

    def test_pass_when_authenticated(self):
        def get_user(request):
            return {"username": "admin"}

        app, *_ = _make_app(auth_check=get_user)
        client = TestClient(app)
        resp = client.get("/admin/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_user_menu_shown(self):
        def get_user(request):
            return {"username": "admin"}

        app, *_ = _make_app(auth_check=get_user)
        client = TestClient(app)
        resp = client.get("/admin/")
        assert "admin" in resp.text

    def test_no_auth_check_allows_access(self):
        app, *_ = _make_app(auth_check=None)
        client = TestClient(app)
        resp = client.get("/admin/")
        assert resp.status_code == 200


# ========================================
# TestAdminMultiModel
# ========================================


class TestAdminMultiModel:
    def test_both_models_accessible(self):
        app, *_ = _make_app()
        client = TestClient(app)
        user_resp = client.get("/admin/user/")
        product_resp = client.get("/admin/product/")
        assert user_resp.status_code == 200
        assert product_resp.status_code == 200

    def test_sidebar_shows_both(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/")
        assert "/admin/user/" in resp.text
        assert "/admin/product/" in resp.text

    def test_product_list_uses_list_fields(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.get("/admin/product/")
        assert "Widget" in resp.text
        assert "Gadget" in resp.text

    def test_create_product(self):
        app, *_ = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/admin/product/new",
            data={"name": "Thingamajig", "price": "5.99"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
