"""Real-time notification system using Server-Sent Events.

Provides ``Notifier`` (server-side channel/queue manager) and
``NotificationStream`` (client-side Toast display component).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from starlette.requests import Request
from starlette.responses import StreamingResponse

from kokage_ui.elements import Component, Div, Raw, Script

_KEEPALIVE_INTERVAL = 15  # seconds


class Notifier:
    """Server-side notification dispatcher.

    Manages per-channel subscriber queues and broadcasts messages as SSE.

    Args:
        default_channel: Default channel name for :meth:`sse_endpoint`.
    """

    def __init__(self, *, default_channel: str = "default") -> None:
        self.default_channel = default_channel
        # channel -> {client_id: asyncio.Queue}
        self._channels: dict[str, dict[str, asyncio.Queue[str | None]]] = {}

    # -- channel management (internal) --

    def _subscribe(self, channel: str) -> tuple[str, asyncio.Queue[str | None]]:
        """Register a new client on *channel* and return (client_id, queue)."""
        client_id = uuid.uuid4().hex[:8]
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._channels.setdefault(channel, {})[client_id] = queue
        return client_id, queue

    def _unsubscribe(self, channel: str, client_id: str) -> None:
        """Remove a client from *channel*, deleting the channel if empty."""
        clients = self._channels.get(channel)
        if clients is None:
            return
        clients.pop(client_id, None)
        if not clients:
            del self._channels[channel]

    # -- public API --

    async def send(self, channel: str, message: str, *, level: str = "info") -> int:
        """Send a notification to all clients on *channel*.

        If *channel* is ``"all"``, broadcasts to every active channel.

        Returns the number of clients that received the message.
        """
        if channel == "all":
            return await self.send_all(message, level=level)

        clients = self._channels.get(channel)
        if not clients:
            return 0

        payload = json.dumps({"message": message, "level": level})
        event = f"event: notification\ndata: {payload}\n\n"
        for queue in clients.values():
            await queue.put(event)
        return len(clients)

    async def send_all(self, message: str, *, level: str = "info") -> int:
        """Broadcast a notification to every active channel.

        Returns the total number of clients reached.
        """
        total = 0
        for channel in list(self._channels):
            clients = self._channels.get(channel)
            if not clients:
                continue
            payload = json.dumps({"message": message, "level": level})
            event = f"event: notification\ndata: {payload}\n\n"
            for queue in clients.values():
                await queue.put(event)
            total += len(clients)
        return total

    @property
    def active_channels(self) -> list[str]:
        """Return the names of channels with at least one subscriber."""
        return list(self._channels)

    def client_count(self, channel: str | None = None) -> int:
        """Return the number of connected clients.

        If *channel* is given, counts only that channel; otherwise all.
        """
        if channel is not None:
            clients = self._channels.get(channel)
            return len(clients) if clients else 0
        return sum(len(c) for c in self._channels.values())

    # -- SSE internals --

    async def _event_generator(
        self,
        channel: str,
        client_id: str,
        queue: asyncio.Queue[str | None],
        request: Request,
    ):
        """Async generator that yields SSE-formatted strings."""
        yield ": connected\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=_KEEPALIVE_INTERVAL)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    break
                yield event
        finally:
            self._unsubscribe(channel, client_id)

    async def sse_endpoint(self, request: Request, channel: str | None = None) -> StreamingResponse:
        """FastAPI/Starlette endpoint handler for SSE connections."""
        ch = channel or self.default_channel
        client_id, queue = self._subscribe(ch)
        return StreamingResponse(
            self._event_generator(ch, client_id, queue, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    def register_routes(self, app: Any, path: str = "/notifications/{channel}") -> None:
        """Register the SSE endpoint on *app*."""
        app.add_api_route(path, self.sse_endpoint, methods=["GET"])


class NotificationStream(Component):
    """Client-side SSE listener that displays incoming notifications as DaisyUI Toasts.

    Args:
        channel: Notification channel to subscribe to.
        url: Explicit SSE endpoint URL. Defaults to ``/notifications/{channel}``.
        position: DaisyUI toast position classes.
        dismiss_ms: Auto-dismiss delay in milliseconds.
    """

    tag = "div"

    def __init__(
        self,
        *,
        channel: str = "default",
        url: str | None = None,
        position: str = "toast-end toast-top",
        dismiss_ms: int = 3000,
        **attrs: Any,
    ) -> None:
        uid = uuid.uuid4().hex[:8]
        sse_url = url or f"/notifications/{channel}"

        script_code = (
            "(function(){"
            f"var src=new EventSource('{sse_url}');"
            "src.addEventListener('notification',function(e){"
            "var d=JSON.parse(e.data);"
            "var cls={'success':'alert-success','error':'alert-error',"
            "'warning':'alert-warning','info':'alert-info'}[d.level]||'alert-info';"
            "var safe=d.message.replace(/</g,'&lt;');"
            "var toast=document.createElement('div');"
            f"toast.className='toast {position} z-50';"
            "toast.innerHTML='<div class=\"alert '+cls+'\"><span>'+safe+'</span></div>';"
            "document.body.appendChild(toast);"
            "setTimeout(function(){"
            "toast.style.transition='opacity 0.3s';"
            "toast.style.opacity='0';"
            f"setTimeout(function(){{toast.remove();}},{300});"
            f"}},{dismiss_ms});"
            "});"
            "})();"
        )

        attrs["id"] = f"kokage-notify-{uid}"
        attrs["style"] = "display:none"
        super().__init__(Script(Raw(script_code)), **attrs)
