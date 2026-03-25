"""Tests for ThreadedAgentView and threaded_agent decorator."""

import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from kokage_ui import (
    AgentEvent,
    InMemoryConversationStore,
    KokageUI,
    Page,
    ThreadedAgentView,
)


# ---------------------------------------------------------------------------
# TestThreadedAgentViewRender
# ---------------------------------------------------------------------------


class TestThreadedAgentViewRender:
    """Test ThreadedAgentView HTML output."""

    def _render(self, **kwargs):
        defaults = {"send_url": "/send", "threads_url": "/api/threads"}
        defaults.update(kwargs)
        return ThreadedAgentView(**defaults).render()

    def test_drawer_structure(self):
        html = self._render()
        assert "drawer lg:drawer-open" in html
        assert "drawer-content" in html
        assert "drawer-side" in html

    def test_thread_list_container(self):
        html = self._render(agent_id="t1")
        assert 't1-thread-list' in html
        assert '<ul id="t1-thread-list"' in html

    def test_new_thread_button(self):
        html = self._render(agent_id="t1")
        assert 't1-new-thread' in html
        assert "+ New Thread" in html

    def test_custom_new_thread_label(self):
        html = self._render(new_thread_label="Create")
        assert "Create" in html

    def test_form_and_input(self):
        html = self._render(agent_id="t1")
        assert 't1-form' in html
        assert 't1-input' in html
        assert 't1-btn' in html

    def test_status_bar(self):
        html = self._render(agent_id="t1", show_status=True)
        assert 't1-status' in html

    def test_no_status_bar(self):
        html = self._render(agent_id="t1", show_status=False)
        assert 't1-status' not in html

    def test_metrics_bar(self):
        html = self._render(agent_id="t1", show_metrics=True)
        assert 't1-metrics' in html

    def test_no_metrics_bar(self):
        html = self._render(agent_id="t1", show_metrics=False)
        assert 't1-metrics' not in html

    def test_custom_agent_id(self):
        html = self._render(agent_id="my-agent")
        assert "my-agent-form" in html
        assert "my-agent-messages" in html

    def test_auto_agent_id(self):
        html = self._render()
        assert "ta-" in html

    def test_send_url_in_js(self):
        html = self._render(send_url="/my/send")
        assert '"/my/send"' in html

    def test_threads_url_in_js(self):
        html = self._render(threads_url="/my/threads")
        assert '"/my/threads"' in html

    def test_xss_escape_placeholder(self):
        html = self._render(placeholder='<script>xss</script>')
        assert '<script>xss</script>' not in html
        assert '&lt;script&gt;' in html

    def test_xss_escape_labels(self):
        html = self._render(send_label='<b>go</b>')
        # Button text in HTML should be escaped
        assert '>&lt;b&gt;go&lt;/b&gt;</button>' in html

    def test_placeholder(self):
        html = self._render(placeholder="Type here...")
        assert "Type here..." in html

    def test_height(self):
        html = self._render(height="80vh")
        assert "80vh" in html

    def test_mobile_hamburger(self):
        html = self._render()
        assert "\u2630" in html  # hamburger character

    def test_drawer_toggle(self):
        html = self._render(agent_id="t1")
        assert 't1-drawer' in html
        assert "drawer-toggle" in html

    def test_sidebar_width(self):
        html = self._render()
        assert "w-64" in html


# ---------------------------------------------------------------------------
# TestThreadedAgentDecorator
# ---------------------------------------------------------------------------


class TestThreadedAgentDecorator:
    """Test the @ui.threaded_agent decorator integration."""

    @pytest.fixture
    def app_and_store(self):
        app = FastAPI()
        ui = KokageUI(app)
        store = InMemoryConversationStore()

        @ui.threaded_agent("/agent", store=store)
        async def my_agent(message: str, thread_id: str):
            yield AgentEvent(type="text", content=f"Echo: {message}")
            yield AgentEvent(type="done")

        return app, store

    @pytest.mark.anyio
    async def test_get_page(self, app_and_store):
        app, _ = app_and_store
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/agent")
            assert resp.status_code == 200
            assert "ThreadedAgentView" in resp.text or "drawer" in resp.text

    @pytest.mark.anyio
    async def test_post_send_stream(self, app_and_store):
        app, store = app_and_store
        thread = await store.create_thread(title="Test")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/agent/send",
                json={"message": "hello", "thread_id": thread.id},
            )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
            # Parse SSE events
            lines = resp.text.strip().split("\n")
            events = []
            for line in lines:
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))
            assert any(e["type"] == "text" for e in events)
            assert any(e["type"] == "done" for e in events)
            text_event = next(e for e in events if e["type"] == "text")
            assert "Echo: hello" in text_event["content"]

    @pytest.mark.anyio
    async def test_threads_api_mounted(self, app_and_store):
        app, _ = app_and_store
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # List threads (should be empty)
            resp = await client.get("/agent/threads")
            assert resp.status_code == 200
            assert resp.json() == []

            # Create thread
            resp = await client.post(
                "/agent/threads",
                json={"title": "Test Thread"},
            )
            assert resp.status_code == 201
            thread = resp.json()
            assert thread["title"] == "Test Thread"
            tid = thread["id"]

            # Get thread
            resp = await client.get(f"/agent/threads/{tid}")
            assert resp.status_code == 200
            assert resp.json()["id"] == tid

            # Update thread
            resp = await client.put(
                f"/agent/threads/{tid}",
                json={"title": "Updated"},
            )
            assert resp.status_code == 200
            assert resp.json()["title"] == "Updated"

            # Add message
            resp = await client.post(
                f"/agent/threads/{tid}/messages",
                json={"role": "user", "content": "hi"},
            )
            assert resp.status_code == 201

            # Get messages
            resp = await client.get(f"/agent/threads/{tid}/messages")
            assert resp.status_code == 200
            assert len(resp.json()) == 1

            # Delete thread
            resp = await client.delete(f"/agent/threads/{tid}")
            assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_custom_threads_prefix(self):
        app = FastAPI()
        ui = KokageUI(app)
        store = InMemoryConversationStore()

        @ui.threaded_agent("/chat", store=store, threads_prefix="/api/convos")
        async def agent_fn(message: str, thread_id: str):
            yield AgentEvent(type="done")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/convos")
            assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_page_contains_drawer(self, app_and_store):
        app, _ = app_and_store
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/agent")
            assert "drawer" in resp.text
            assert "/agent/send" in resp.text
            assert "/agent/threads" in resp.text

    @pytest.mark.anyio
    async def test_page_includes_marked_js(self, app_and_store):
        app, _ = app_and_store
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/agent")
            assert "marked" in resp.text

    @pytest.mark.anyio
    async def test_page_includes_highlightjs(self, app_and_store):
        app, _ = app_and_store
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/agent")
            assert "highlight" in resp.text


# ---------------------------------------------------------------------------
# TestPageAutoDetect
# ---------------------------------------------------------------------------


class TestPageAutoDetect:
    """Test that Page auto-detects ThreadedAgentView for CDN includes."""

    def test_auto_includes_marked_and_hljs(self):
        view = ThreadedAgentView(send_url="/send", threads_url="/threads")
        page = Page(view, title="Test")
        html = page.render()
        assert "marked" in html
        assert "highlight" in html
