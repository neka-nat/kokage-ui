"""Tests for ui.chat() and ui.agent() decorators."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kokage_ui import KokageUI
from kokage_ui.ai.agent import AgentEvent


@pytest.fixture
def app_and_ui():
    app = FastAPI()
    ui = KokageUI(app)
    return app, ui


class TestUiChat:
    def test_creates_page_and_api_routes(self, app_and_ui):
        app, ui = app_and_ui

        @ui.chat("/chat")
        async def my_chat(message: str):
            yield "Hello "
            yield "World"

        client = TestClient(app)

        # Page route exists and returns HTML
        resp = client.get("/chat")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        html = resp.text
        assert "chat" in html.lower()

        # API route exists and returns SSE
        resp = client.post("/chat/send", json={"message": "hi"})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_page_includes_marked_and_highlightjs(self, app_and_ui):
        app, ui = app_and_ui

        @ui.chat("/chat")
        async def my_chat(message: str):
            yield "test"

        client = TestClient(app)
        html = client.get("/chat").text
        assert "marked.min.js" in html
        assert "highlight.min.js" in html

    def test_send_url_matches_api_path(self, app_and_ui):
        app, ui = app_and_ui

        @ui.chat("/chat")
        async def my_chat(message: str):
            yield "test"

        client = TestClient(app)
        html = client.get("/chat").text
        assert "/chat/send" in html

    def test_sse_stream_content(self, app_and_ui):
        app, ui = app_and_ui

        @ui.chat("/chat")
        async def my_chat(message: str):
            yield f"Echo: {message}"

        client = TestClient(app)
        resp = client.post("/chat/send", json={"message": "hello"})
        text = resp.text
        assert '"token"' in text
        assert "Echo: hello" in text
        assert '"done": true' in text

    def test_custom_params(self, app_and_ui):
        app, ui = app_and_ui

        @ui.chat("/chat", placeholder="Ask me...", send_label="Go", title="My Chat")
        async def my_chat(message: str):
            yield "ok"

        client = TestClient(app)
        html = client.get("/chat").text
        assert "Ask me..." in html
        assert "Go" in html
        assert "My Chat" in html


class TestUiAgent:
    def test_creates_page_and_api_routes(self, app_and_ui):
        app, ui = app_and_ui

        @ui.agent("/agent")
        async def my_agent(message: str):
            yield AgentEvent(type="text", content="Hi")
            yield AgentEvent(type="done")

        client = TestClient(app)

        # Page route
        resp = client.get("/agent")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

        # API route
        resp = client.post("/agent/send", json={"message": "hi"})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_page_includes_marked_and_highlightjs(self, app_and_ui):
        app, ui = app_and_ui

        @ui.agent("/agent")
        async def my_agent(message: str):
            yield AgentEvent(type="done")

        client = TestClient(app)
        html = client.get("/agent").text
        assert "marked.min.js" in html
        assert "highlight.min.js" in html

    def test_send_url_matches_api_path(self, app_and_ui):
        app, ui = app_and_ui

        @ui.agent("/agent")
        async def my_agent(message: str):
            yield AgentEvent(type="done")

        client = TestClient(app)
        html = client.get("/agent").text
        assert "/agent/send" in html

    def test_sse_stream_content(self, app_and_ui):
        app, ui = app_and_ui

        @ui.agent("/agent")
        async def my_agent(message: str):
            yield AgentEvent(type="text", content=f"Got: {message}")
            yield AgentEvent(type="done", metrics={"tokens": 10})

        client = TestClient(app)
        resp = client.post("/agent/send", json={"message": "test"})
        text = resp.text
        assert "Got: test" in text
        assert '"type"' in text

    def test_custom_params(self, app_and_ui):
        app, ui = app_and_ui

        @ui.agent("/agent", agent_name="Bot", placeholder="Query...", title="My Agent")
        async def my_agent(message: str):
            yield AgentEvent(type="done")

        client = TestClient(app)
        html = client.get("/agent").text
        assert "Query..." in html
        assert "My Agent" in html

    def test_status_and_metrics_bars(self, app_and_ui):
        app, ui = app_and_ui

        @ui.agent("/agent", show_status=True, show_metrics=True)
        async def my_agent(message: str):
            yield AgentEvent(type="done")

        client = TestClient(app)
        html = client.get("/agent").text
        assert "-status" in html
        assert "-metrics" in html

    def test_no_status_bar(self, app_and_ui):
        app, ui = app_and_ui

        @ui.agent("/agent", show_status=False)
        async def my_agent(message: str):
            yield AgentEvent(type="done")

        client = TestClient(app)
        html = client.get("/agent").text
        # Status bar div should not be in the HTML body (before <script>)
        body_html = html.split("<script>")[0]
        assert "-status" not in body_html
