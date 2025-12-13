"""Integration tests with FastAPI TestClient."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from kokage_ui import (
    AutoRefresh,
    Card,
    DaisyButton,
    Div,
    H1,
    KokageUI,
    P,
    Page,
    SearchFilter,
    Stat,
    Stats,
)


@pytest.fixture
def app():
    app = FastAPI()
    ui = KokageUI(app)

    @ui.page("/")
    def index():
        return Page(
            Div(H1("Hello kokage"), cls="container"),
            title="Test Page",
        )

    @ui.page("/card")
    def card_page():
        return Page(
            Card(P("Content"), title="Test Card"),
            title="Card Page",
        )

    @ui.fragment("/api/items")
    def items_fragment(request: Request):
        return Div(P("Item 1"), P("Item 2"), id="items")

    @ui.fragment("/api/open", htmx_only=False)
    def open_fragment(request: Request):
        return Div("Open", id="open")

    @ui.fragment("/api/stats")
    def stats_fragment(request: Request):
        return Stats(
            Stat(title="Users", value="100"),
        )

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestPageRoutes:
    def test_index_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "Hello kokage" in response.text
        assert "Test Page" in response.text

    def test_index_content_type(self, client):
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_card_page(self, client):
        response = client.get("/card")
        assert response.status_code == 200
        assert "card-title" in response.text
        assert "Test Card" in response.text

    def test_page_includes_htmx(self, client):
        response = client.get("/")
        assert "htmx.min.js" in response.text

    def test_page_includes_daisyui(self, client):
        response = client.get("/")
        assert "daisyui" in response.text


class TestFragmentRoutes:
    def test_fragment_with_htmx_header(self, client):
        response = client.get("/api/items", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert '<div id="items">' in response.text
        assert "<!DOCTYPE html>" not in response.text

    def test_fragment_without_htmx_header_rejected(self, client):
        response = client.get("/api/items")
        assert response.status_code == 403

    def test_fragment_htmx_only_false(self, client):
        response = client.get("/api/open")
        assert response.status_code == 200
        assert "Open" in response.text

    def test_stats_fragment(self, client):
        response = client.get("/api/stats", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "stat-value" in response.text
        assert "100" in response.text


class TestStaticFiles:
    def test_htmx_js_served(self, client):
        response = client.get("/_kokage/static/htmx.min.js")
        assert response.status_code == 200
        assert len(response.content) > 0
