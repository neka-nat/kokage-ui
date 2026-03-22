"""Conversation store for persistent message history and threads.

Provides :class:`Thread` and :class:`Message` models along with
:class:`ConversationStore` (ABC) and :class:`InMemoryConversationStore`.

Example::

    from kokage_ui.ai.conversation import InMemoryConversationStore

    store = InMemoryConversationStore()
    thread = await store.create_thread(title="My Chat")
    await store.add_message(thread.id, role="user", content="Hello!")
    messages = await store.get_messages(thread.id)
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from kokage_ui.ai.agent import ToolCall


class Thread(BaseModel):
    """A conversation thread.

    Args:
        id: Unique thread identifier.
        title: Display title.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last update timestamp.
    """

    id: str = ""
    title: str = ""
    created_at: str = ""
    updated_at: str = ""


class Message(BaseModel):
    """A single message in a conversation thread.

    Args:
        id: Unique message identifier.
        thread_id: Parent thread ID.
        role: Message role — ``"user"`` or ``"assistant"``.
        content: Message text content.
        tool_calls: Optional tool call records (assistant messages).
        created_at: ISO 8601 creation timestamp.
    """

    id: str = ""
    thread_id: str = ""
    role: str = ""
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    created_at: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class ConversationStore(ABC):
    """Abstract conversation store interface."""

    # -- Thread operations --

    @abstractmethod
    async def create_thread(self, title: str = "") -> Thread:
        """Create a new thread."""

    @abstractmethod
    async def list_threads(self) -> list[Thread]:
        """List all threads, most recent first."""

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Thread | None:
        """Get a thread by ID."""

    @abstractmethod
    async def update_thread(self, thread_id: str, title: str) -> Thread | None:
        """Update a thread's title."""

    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and all its messages."""

    # -- Message operations --

    @abstractmethod
    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str = "",
        tool_calls: list[ToolCall] | None = None,
    ) -> Message:
        """Add a message to a thread."""

    @abstractmethod
    async def get_messages(self, thread_id: str) -> list[Message]:
        """Get all messages in a thread, oldest first."""

    @abstractmethod
    async def clear_messages(self, thread_id: str) -> None:
        """Delete all messages in a thread (keep the thread)."""

    # -- Convenience --

    def mount(self, app: "FastAPI", prefix: str = "/api/threads") -> None:
        """Register REST API endpoints for threads and messages.

        Endpoints:
            - ``GET  {prefix}``                     — list threads
            - ``POST {prefix}``                     — create thread
            - ``GET  {prefix}/{thread_id}``         — get thread
            - ``PUT  {prefix}/{thread_id}``         — update thread title
            - ``DELETE {prefix}/{thread_id}``       — delete thread
            - ``GET  {prefix}/{thread_id}/messages`` — get messages
            - ``POST {prefix}/{thread_id}/messages`` — add message
            - ``DELETE {prefix}/{thread_id}/messages`` — clear messages
        """
        import fastapi
        from starlette.responses import JSONResponse

        prefix = prefix.rstrip("/")
        store = self

        @app.get(prefix)
        async def _list_threads():
            return await store.list_threads()

        @app.post(prefix, status_code=201)
        async def _create_thread(request: fastapi.Request):
            data = await request.json()
            return await store.create_thread(title=data.get("title", ""))

        @app.get(f"{prefix}/{{thread_id}}")
        async def _get_thread(thread_id: str):
            thread = await store.get_thread(thread_id)
            if thread is None:
                return JSONResponse({"detail": "Thread not found"}, status_code=404)
            return thread

        @app.put(f"{prefix}/{{thread_id}}")
        async def _update_thread(thread_id: str, request: fastapi.Request):
            data = await request.json()
            thread = await store.update_thread(thread_id, title=data.get("title", ""))
            if thread is None:
                return JSONResponse({"detail": "Thread not found"}, status_code=404)
            return thread

        @app.delete(f"{prefix}/{{thread_id}}")
        async def _delete_thread(thread_id: str):
            await store.delete_thread(thread_id)

        @app.get(f"{prefix}/{{thread_id}}/messages")
        async def _get_messages(thread_id: str):
            return await store.get_messages(thread_id)

        @app.post(f"{prefix}/{{thread_id}}/messages", status_code=201)
        async def _add_message(thread_id: str, request: fastapi.Request):
            data = await request.json()
            return await store.add_message(
                thread_id,
                role=data.get("role", "user"),
                content=data.get("content", ""),
            )

        @app.delete(f"{prefix}/{{thread_id}}/messages")
        async def _clear_messages(thread_id: str):
            await store.clear_messages(thread_id)


class InMemoryConversationStore(ConversationStore):
    """In-memory conversation store for development and testing."""

    def __init__(self) -> None:
        self._threads: dict[str, Thread] = {}
        self._messages: dict[str, list[Message]] = {}

    async def create_thread(self, title: str = "") -> Thread:
        now = _now_iso()
        thread = Thread(id=_new_id(), title=title or "New Thread", created_at=now, updated_at=now)
        self._threads[thread.id] = thread
        self._messages[thread.id] = []
        return thread

    async def list_threads(self) -> list[Thread]:
        return sorted(self._threads.values(), key=lambda t: t.updated_at, reverse=True)

    async def get_thread(self, thread_id: str) -> Thread | None:
        return self._threads.get(thread_id)

    async def update_thread(self, thread_id: str, title: str) -> Thread | None:
        thread = self._threads.get(thread_id)
        if thread is None:
            return None
        thread = thread.model_copy(update={"title": title, "updated_at": _now_iso()})
        self._threads[thread_id] = thread
        return thread

    async def delete_thread(self, thread_id: str) -> bool:
        if thread_id not in self._threads:
            return False
        del self._threads[thread_id]
        self._messages.pop(thread_id, None)
        return True

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str = "",
        tool_calls: list[ToolCall] | None = None,
    ) -> Message:
        msg = Message(
            id=_new_id(),
            thread_id=thread_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            created_at=_now_iso(),
        )
        if thread_id not in self._messages:
            self._messages[thread_id] = []
        self._messages[thread_id].append(msg)
        # Update thread's updated_at
        if thread_id in self._threads:
            t = self._threads[thread_id]
            self._threads[thread_id] = t.model_copy(update={"updated_at": msg.created_at})
        return msg

    async def get_messages(self, thread_id: str) -> list[Message]:
        return list(self._messages.get(thread_id, []))

    async def clear_messages(self, thread_id: str) -> None:
        if thread_id in self._messages:
            self._messages[thread_id] = []
