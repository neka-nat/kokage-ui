"""Tests for kokage_ui.notifications module."""

from __future__ import annotations

import asyncio
import json

import pytest
from starlette.responses import StreamingResponse

from kokage_ui.notifications import Notifier, NotificationStream


# ---------------------------------------------------------------------------
# Notifier – init & channel management
# ---------------------------------------------------------------------------


class TestNotifier:
    def test_init_default_channel(self):
        n = Notifier()
        assert n.default_channel == "default"

    def test_init_custom_channel(self):
        n = Notifier(default_channel="alerts")
        assert n.default_channel == "alerts"

    def test_subscribe_creates_channel(self):
        n = Notifier()
        cid, q = n._subscribe("ch1")
        assert "ch1" in n._channels
        assert cid in n._channels["ch1"]
        assert isinstance(q, asyncio.Queue)

    def test_unsubscribe_removes_client(self):
        n = Notifier()
        cid, _ = n._subscribe("ch1")
        n._unsubscribe("ch1", cid)
        assert "ch1" not in n._channels

    def test_unsubscribe_keeps_channel_with_other_clients(self):
        n = Notifier()
        cid1, _ = n._subscribe("ch1")
        cid2, _ = n._subscribe("ch1")
        n._unsubscribe("ch1", cid1)
        assert "ch1" in n._channels
        assert cid2 in n._channels["ch1"]

    def test_unsubscribe_nonexistent_channel(self):
        n = Notifier()
        n._unsubscribe("nope", "xyz")  # should not raise

    def test_active_channels(self):
        n = Notifier()
        assert n.active_channels == []
        n._subscribe("a")
        n._subscribe("b")
        assert sorted(n.active_channels) == ["a", "b"]

    def test_client_count_all(self):
        n = Notifier()
        assert n.client_count() == 0
        n._subscribe("a")
        n._subscribe("a")
        n._subscribe("b")
        assert n.client_count() == 3

    def test_client_count_per_channel(self):
        n = Notifier()
        assert n.client_count("a") == 0
        n._subscribe("a")
        n._subscribe("a")
        n._subscribe("b")
        assert n.client_count("a") == 2
        assert n.client_count("b") == 1


# ---------------------------------------------------------------------------
# Notifier – send / send_all
# ---------------------------------------------------------------------------


class TestNotifierSend:
    @pytest.mark.anyio
    async def test_send_to_channel(self):
        n = Notifier()
        _, q = n._subscribe("ch")
        count = await n.send("ch", "hello", level="success")
        assert count == 1
        event = q.get_nowait()
        assert "event: notification" in event
        data_line = [l for l in event.splitlines() if l.startswith("data:")][0]
        payload = json.loads(data_line[len("data: "):])
        assert payload == {"message": "hello", "level": "success"}

    @pytest.mark.anyio
    async def test_send_default_level(self):
        n = Notifier()
        _, q = n._subscribe("ch")
        await n.send("ch", "msg")
        event = q.get_nowait()
        data_line = [l for l in event.splitlines() if l.startswith("data:")][0]
        payload = json.loads(data_line[len("data: "):])
        assert payload["level"] == "info"

    @pytest.mark.anyio
    async def test_send_no_subscribers(self):
        n = Notifier()
        count = await n.send("empty", "msg")
        assert count == 0

    @pytest.mark.anyio
    async def test_send_all_broadcasts(self):
        n = Notifier()
        _, q1 = n._subscribe("a")
        _, q2 = n._subscribe("b")
        count = await n.send("all", "broadcast!")
        assert count == 2
        assert not q1.empty()
        assert not q2.empty()

    @pytest.mark.anyio
    async def test_send_all_method(self):
        n = Notifier()
        _, q1 = n._subscribe("a")
        _, q2 = n._subscribe("a")
        _, q3 = n._subscribe("b")
        count = await n.send_all("hi")
        assert count == 3

    @pytest.mark.anyio
    async def test_send_multiple_clients(self):
        n = Notifier()
        _, q1 = n._subscribe("ch")
        _, q2 = n._subscribe("ch")
        count = await n.send("ch", "msg")
        assert count == 2
        assert not q1.empty()
        assert not q2.empty()


# ---------------------------------------------------------------------------
# Notifier – _event_generator
# ---------------------------------------------------------------------------


class _FakeRequest:
    """Minimal request stub for testing."""

    def __init__(self, *, disconnected: bool = False):
        self._disconnected = disconnected

    async def is_disconnected(self) -> bool:
        return self._disconnected


class TestEventGenerator:
    @pytest.mark.anyio
    async def test_initial_comment(self):
        n = Notifier()
        cid, q = n._subscribe("ch")
        req = _FakeRequest()
        gen = n._event_generator("ch", cid, q, req)
        first = await gen.__anext__()
        assert first == ": connected\n\n"
        # cleanup
        await q.put(None)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    @pytest.mark.anyio
    async def test_message_forwarding(self):
        n = Notifier()
        cid, q = n._subscribe("ch")
        req = _FakeRequest()
        gen = n._event_generator("ch", cid, q, req)

        # consume connected comment
        await gen.__anext__()

        payload = json.dumps({"message": "hi", "level": "info"})
        event = f"event: notification\ndata: {payload}\n\n"
        await q.put(event)
        result = await gen.__anext__()
        assert result == event

        # stop
        await q.put(None)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    @pytest.mark.anyio
    async def test_sentinel_stops(self):
        n = Notifier()
        cid, q = n._subscribe("ch")
        req = _FakeRequest()
        gen = n._event_generator("ch", cid, q, req)
        await gen.__anext__()  # connected

        await q.put(None)
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    @pytest.mark.anyio
    async def test_cleanup_on_stop(self):
        n = Notifier()
        cid, q = n._subscribe("ch")
        req = _FakeRequest()
        gen = n._event_generator("ch", cid, q, req)
        await gen.__anext__()  # connected

        await q.put(None)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

        # client should be unsubscribed
        assert n.client_count("ch") == 0

    @pytest.mark.anyio
    async def test_disconnect_stops(self):
        n = Notifier()
        cid, q = n._subscribe("ch")
        req = _FakeRequest(disconnected=True)
        gen = n._event_generator("ch", cid, q, req)
        await gen.__anext__()  # connected

        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()


# ---------------------------------------------------------------------------
# NotificationStream – rendering
# ---------------------------------------------------------------------------


class TestNotificationStream:
    def test_hidden_div(self):
        ns = NotificationStream(channel="test")
        html = ns.render()
        assert 'style="display:none"' in html
        assert 'id="kokage-notify-' in html

    def test_contains_script(self):
        ns = NotificationStream(channel="test")
        html = ns.render()
        assert "<script>" in html
        assert "EventSource" in html

    def test_default_url(self):
        ns = NotificationStream(channel="admin")
        html = ns.render()
        assert "/notifications/admin" in html

    def test_custom_url(self):
        ns = NotificationStream(channel="admin", url="/custom/sse")
        html = ns.render()
        assert "/custom/sse" in html
        assert "/notifications/admin" not in html

    def test_position(self):
        ns = NotificationStream(channel="ch", position="toast-start toast-bottom")
        html = ns.render()
        assert "toast-start toast-bottom" in html

    def test_dismiss_ms(self):
        ns = NotificationStream(channel="ch", dismiss_ms=5000)
        html = ns.render()
        assert "5000" in html

    def test_xss_escape_in_script(self):
        ns = NotificationStream(channel="ch")
        html = ns.render()
        # The script must include the XSS escape for messages
        assert "replace(/</g,'&lt;')" in html

    def test_notification_event_listener(self):
        ns = NotificationStream(channel="ch")
        html = ns.render()
        assert "addEventListener('notification'" in html

    def test_auto_dismiss(self):
        ns = NotificationStream(channel="ch")
        html = ns.render()
        assert "toast.remove()" in html
        assert "opacity" in html


# ---------------------------------------------------------------------------
# SSE integration (register_routes / endpoint)
# ---------------------------------------------------------------------------


class TestSSEIntegration:
    def test_register_routes(self):
        routes = []

        class FakeApp:
            def add_api_route(self, path, endpoint, **kw):
                routes.append((path, endpoint, kw))

        n = Notifier()
        n.register_routes(FakeApp())
        assert len(routes) == 1
        assert routes[0][0] == "/notifications/{channel}"

    def test_register_routes_custom_path(self):
        routes = []

        class FakeApp:
            def add_api_route(self, path, endpoint, **kw):
                routes.append((path, endpoint, kw))

        n = Notifier()
        n.register_routes(FakeApp(), path="/sse/{channel}")
        assert routes[0][0] == "/sse/{channel}"

    @pytest.mark.anyio
    async def test_sse_endpoint_returns_streaming_response(self):
        n = Notifier()
        req = _FakeRequest()
        resp = await n.sse_endpoint(req, channel="test")
        assert isinstance(resp, StreamingResponse)
        assert resp.media_type == "text/event-stream"

    @pytest.mark.anyio
    async def test_sse_endpoint_uses_default_channel(self):
        n = Notifier(default_channel="mydef")
        req = _FakeRequest()
        await n.sse_endpoint(req)
        assert "mydef" in n.active_channels

    @pytest.mark.anyio
    async def test_sse_endpoint_headers(self):
        n = Notifier()
        req = _FakeRequest()
        resp = await n.sse_endpoint(req, channel="test")
        assert resp.headers["Cache-Control"] == "no-cache"
        assert resp.headers["X-Accel-Buffering"] == "no"
