"""Tests for DevToolbar middleware and rendering."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from kokage_ui import Div, H1, InMemoryStorage, KokageUI, P, Page


# --- Fixtures ---


@pytest.fixture
def debug_app():
    """FastAPI app with debug=True."""
    app = FastAPI()
    ui = KokageUI(app, debug=True)

    @ui.page("/")
    def index():
        return Page(H1("Hello"), title="Home")

    @ui.page("/about", methods=["GET", "POST"])
    def about():
        return Page(P("About"), title="About")

    @ui.fragment("/api/items")
    def items_fragment(request: Request):
        return Div(P("Item 1"), id="items")

    return app


@pytest.fixture
def debug_client(debug_app):
    return TestClient(debug_app)


@pytest.fixture
def no_debug_app():
    """FastAPI app with debug=False (default)."""
    app = FastAPI()
    ui = KokageUI(app)

    @ui.page("/")
    def index():
        return Page(H1("Hello"), title="Home")

    return app


@pytest.fixture
def no_debug_client(no_debug_app):
    return TestClient(no_debug_app)


# --- TestRenderToolbar ---


class TestRenderToolbar:
    """Tests for toolbar rendering content."""

    def test_info_bar_method_and_path(self, debug_client):
        resp = debug_client.get("/")
        assert "GET /" in resp.text

    def test_info_bar_response_time(self, debug_client):
        resp = debug_client.get("/")
        # Should contain a time value like "⏱ 1.2ms"
        assert "⏱" in resp.text
        assert "ms" in resp.text

    def test_info_bar_html_size(self, debug_client):
        resp = debug_client.get("/")
        assert "📄" in resp.text
        assert "KB" in resp.text

    def test_htmx_indicator_no_htmx(self, debug_client):
        resp = debug_client.get("/")
        assert "htmx: ✗" in resp.text

    def test_htmx_indicator_with_htmx(self, debug_client):
        resp = debug_client.get("/", headers={"HX-Request": "true"})
        assert "htmx: ✓" in resp.text

    def test_routes_table_contains_registered_routes(self, debug_client):
        resp = debug_client.get("/")
        body = resp.text
        # Should show page routes
        assert "index" in body
        assert "about" in body

    def test_routes_table_shows_fragment(self, debug_client):
        resp = debug_client.get("/")
        assert "/api/items" in resp.text
        assert "fragment" in resp.text

    def test_current_route_highlight(self, debug_client):
        resp = debug_client.get("/about")
        # Current route should have highlight style and marker
        assert "← current" in resp.text

    def test_request_tab_query_params(self, debug_client):
        resp = debug_client.get("/?foo=bar&baz=123")
        body = resp.text
        assert "foo" in body
        assert "bar" in body
        assert "baz" in body
        assert "123" in body

    def test_request_tab_no_query_params(self, debug_client):
        resp = debug_client.get("/")
        assert "No query parameters" in resp.text

    def test_request_tab_headers(self, debug_client):
        resp = debug_client.get("/", headers={"X-Custom": "test-value"})
        assert "x-custom" in resp.text
        assert "test-value" in resp.text

    def test_htmx_tab_present(self, debug_client):
        resp = debug_client.get("/")
        assert "htmx.logAll()" in resp.text
        assert "kokageToggleHtmxLog" in resp.text


# --- TestDevToolbarMiddleware ---


class TestDevToolbarMiddleware:
    """Tests for middleware injection behavior."""

    def test_injects_into_html_response(self, debug_client):
        resp = debug_client.get("/")
        assert resp.status_code == 200
        assert "kokage-devtoolbar" in resp.text

    def test_skips_fragment_no_body_tag(self, debug_client):
        resp = debug_client.get(
            "/api/items", headers={"HX-Request": "true"}
        )
        assert resp.status_code == 200
        assert "kokage-devtoolbar" not in resp.text

    def test_preserves_response_status(self, debug_client):
        resp = debug_client.get("/")
        assert resp.status_code == 200

    def test_toolbar_before_body_close(self, debug_client):
        resp = debug_client.get("/")
        body = resp.text
        toolbar_pos = body.find("kokage-devtoolbar")
        body_close_pos = body.find("</body>")
        assert toolbar_pos < body_close_pos

    def test_skips_non_html_response(self):
        app = FastAPI()
        KokageUI(app, debug=True)

        @app.get("/json")
        def json_endpoint():
            return {"key": "value"}

        client = TestClient(app)
        resp = client.get("/json")
        assert resp.status_code == 200
        assert "kokage-devtoolbar" not in resp.text


# --- TestKokageUIDebug ---


class TestKokageUIDebug:
    """Tests for KokageUI debug flag and route tracking."""

    def test_debug_false_no_toolbar(self, no_debug_client):
        resp = no_debug_client.get("/")
        assert resp.status_code == 200
        assert "kokage-devtoolbar" not in resp.text

    def test_debug_true_toolbar_present(self, debug_client):
        resp = debug_client.get("/")
        assert resp.status_code == 200
        assert "kokage-devtoolbar" in resp.text

    def test_route_tracking_page(self):
        app = FastAPI()
        ui = KokageUI(app, debug=True)

        @ui.page("/test")
        def test_page():
            return Page(P("test"))

        routes = [r for r in ui._routes if r["type"] == "page"]
        assert any(r["path"] == "/test" for r in routes)
        assert any(r["name"] == "test_page" for r in routes)

    def test_route_tracking_fragment(self):
        app = FastAPI()
        ui = KokageUI(app, debug=True)

        @ui.fragment("/api/test")
        def test_frag(request: Request):
            return Div("test")

        routes = [r for r in ui._routes if r["type"] == "fragment"]
        assert any(r["path"] == "/api/test" for r in routes)

    def test_route_tracking_crud(self):
        class Item(BaseModel):
            id: int = 0
            name: str = ""

        app = FastAPI()
        ui = KokageUI(app, debug=True)
        ui.crud("/items", model=Item, storage=InMemoryStorage(Item))

        crud_routes = [r for r in ui._routes if r["type"] == "crud"]
        paths = [r["path"] for r in crud_routes]
        assert "/items" in paths
        assert "/items/_list" in paths
        assert "/items/new" in paths
        assert "/items/{id}" in paths

    def test_no_routes_when_debug_false(self):
        app = FastAPI()
        ui = KokageUI(app, debug=False)

        @ui.page("/test")
        def test_page():
            return Page(P("test"))

        assert len(ui._routes) == 0

    def test_route_tracking_methods(self):
        app = FastAPI()
        ui = KokageUI(app, debug=True)

        @ui.page("/multi", methods=["GET", "POST"])
        def multi():
            return Page(P("test"))

        route = next(r for r in ui._routes if r["path"] == "/multi")
        assert route["methods"] == ["GET", "POST"]
