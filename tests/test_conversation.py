"""Tests for ConversationStore, Thread, and Message."""

import pytest

from kokage_ui.ai.conversation import (
    ConversationStore,
    InMemoryConversationStore,
    Message,
    Thread,
)


@pytest.fixture
def store():
    return InMemoryConversationStore()


# ==================== Thread ====================


class TestThread:
    def test_defaults(self):
        t = Thread()
        assert t.id == ""
        assert t.title == ""

    def test_with_values(self):
        t = Thread(id="abc", title="My Thread", created_at="2026-01-01T00:00:00")
        assert t.id == "abc"
        assert t.title == "My Thread"


# ==================== Message ====================


class TestMessage:
    def test_defaults(self):
        m = Message()
        assert m.role == ""
        assert m.content == ""
        assert m.tool_calls is None

    def test_with_tool_calls(self):
        from kokage_ui.ai.agent import ToolCall

        m = Message(
            thread_id="t1",
            role="assistant",
            content="Result",
            tool_calls=[ToolCall(name="search", input={"q": "test"})],
        )
        assert len(m.tool_calls) == 1
        assert m.tool_calls[0].name == "search"


# ==================== InMemoryConversationStore: Threads ====================


class TestCreateThread:
    @pytest.mark.asyncio
    async def test_creates_thread(self, store):
        thread = await store.create_thread(title="Test")
        assert thread.title == "Test"
        assert thread.id != ""
        assert thread.created_at != ""
        assert thread.updated_at != ""

    @pytest.mark.asyncio
    async def test_default_title(self, store):
        thread = await store.create_thread()
        assert thread.title == "New Thread"

    @pytest.mark.asyncio
    async def test_unique_ids(self, store):
        t1 = await store.create_thread()
        t2 = await store.create_thread()
        assert t1.id != t2.id


class TestListThreads:
    @pytest.mark.asyncio
    async def test_empty(self, store):
        threads = await store.list_threads()
        assert threads == []

    @pytest.mark.asyncio
    async def test_returns_all(self, store):
        await store.create_thread(title="A")
        await store.create_thread(title="B")
        threads = await store.list_threads()
        assert len(threads) == 2

    @pytest.mark.asyncio
    async def test_most_recent_first(self, store):
        t1 = await store.create_thread(title="First")
        t2 = await store.create_thread(title="Second")
        threads = await store.list_threads()
        assert threads[0].id == t2.id


class TestGetThread:
    @pytest.mark.asyncio
    async def test_existing(self, store):
        created = await store.create_thread(title="Test")
        found = await store.get_thread(created.id)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_not_found(self, store):
        result = await store.get_thread("nonexistent")
        assert result is None


class TestUpdateThread:
    @pytest.mark.asyncio
    async def test_updates_title(self, store):
        thread = await store.create_thread(title="Old")
        updated = await store.update_thread(thread.id, title="New")
        assert updated is not None
        assert updated.title == "New"
        assert updated.updated_at >= thread.updated_at

    @pytest.mark.asyncio
    async def test_not_found(self, store):
        result = await store.update_thread("nonexistent", title="X")
        assert result is None


class TestDeleteThread:
    @pytest.mark.asyncio
    async def test_deletes_thread(self, store):
        thread = await store.create_thread()
        result = await store.delete_thread(thread.id)
        assert result is True
        assert await store.get_thread(thread.id) is None

    @pytest.mark.asyncio
    async def test_deletes_messages_too(self, store):
        thread = await store.create_thread()
        await store.add_message(thread.id, "user", "Hello")
        await store.delete_thread(thread.id)
        messages = await store.get_messages(thread.id)
        assert messages == []

    @pytest.mark.asyncio
    async def test_not_found(self, store):
        result = await store.delete_thread("nonexistent")
        assert result is False


# ==================== InMemoryConversationStore: Messages ====================


class TestAddMessage:
    @pytest.mark.asyncio
    async def test_adds_message(self, store):
        thread = await store.create_thread()
        msg = await store.add_message(thread.id, "user", "Hello")
        assert msg.id != ""
        assert msg.thread_id == thread.id
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.created_at != ""

    @pytest.mark.asyncio
    async def test_with_tool_calls(self, store):
        from kokage_ui.ai.agent import ToolCall

        thread = await store.create_thread()
        tc = [ToolCall(name="search", input="q")]
        msg = await store.add_message(thread.id, "assistant", "Result", tool_calls=tc)
        assert msg.tool_calls is not None
        assert len(msg.tool_calls) == 1

    @pytest.mark.asyncio
    async def test_updates_thread_timestamp(self, store):
        thread = await store.create_thread()
        original = thread.updated_at
        await store.add_message(thread.id, "user", "Hello")
        updated_thread = await store.get_thread(thread.id)
        assert updated_thread.updated_at >= original

    @pytest.mark.asyncio
    async def test_orphan_message(self, store):
        """Adding message to non-existent thread should still work."""
        msg = await store.add_message("orphan", "user", "Hello")
        assert msg.thread_id == "orphan"


class TestGetMessages:
    @pytest.mark.asyncio
    async def test_empty(self, store):
        thread = await store.create_thread()
        messages = await store.get_messages(thread.id)
        assert messages == []

    @pytest.mark.asyncio
    async def test_returns_in_order(self, store):
        thread = await store.create_thread()
        await store.add_message(thread.id, "user", "First")
        await store.add_message(thread.id, "assistant", "Second")
        messages = await store.get_messages(thread.id)
        assert len(messages) == 2
        assert messages[0].content == "First"
        assert messages[1].content == "Second"

    @pytest.mark.asyncio
    async def test_returns_copy(self, store):
        """Returned list should be a copy, not a reference."""
        thread = await store.create_thread()
        await store.add_message(thread.id, "user", "Hello")
        msgs1 = await store.get_messages(thread.id)
        msgs2 = await store.get_messages(thread.id)
        assert msgs1 is not msgs2

    @pytest.mark.asyncio
    async def test_nonexistent_thread(self, store):
        messages = await store.get_messages("nonexistent")
        assert messages == []


class TestClearMessages:
    @pytest.mark.asyncio
    async def test_clears_messages(self, store):
        thread = await store.create_thread()
        await store.add_message(thread.id, "user", "Hello")
        await store.add_message(thread.id, "assistant", "Hi")
        await store.clear_messages(thread.id)
        messages = await store.get_messages(thread.id)
        assert messages == []

    @pytest.mark.asyncio
    async def test_thread_still_exists(self, store):
        thread = await store.create_thread(title="Keep me")
        await store.add_message(thread.id, "user", "Hello")
        await store.clear_messages(thread.id)
        found = await store.get_thread(thread.id)
        assert found is not None
        assert found.title == "Keep me"

    @pytest.mark.asyncio
    async def test_nonexistent_thread(self, store):
        """Should not raise."""
        await store.clear_messages("nonexistent")


# ==================== mount ====================


class TestMount:
    @pytest.mark.asyncio
    async def test_thread_crud_endpoints(self, store):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        app = FastAPI()
        store.mount(app, prefix="/api/threads")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create
            resp = await client.post("/api/threads", json={"title": "Test Thread"})
            assert resp.status_code == 201
            thread = resp.json()
            tid = thread["id"]
            assert thread["title"] == "Test Thread"

            # List
            resp = await client.get("/api/threads")
            assert resp.status_code == 200
            assert len(resp.json()) == 1

            # Get
            resp = await client.get(f"/api/threads/{tid}")
            assert resp.status_code == 200
            assert resp.json()["title"] == "Test Thread"

            # Update
            resp = await client.put(f"/api/threads/{tid}", json={"title": "Updated"})
            assert resp.status_code == 200
            assert resp.json()["title"] == "Updated"

            # Get not found
            resp = await client.get("/api/threads/nonexistent")
            assert resp.status_code == 404

            # Delete
            resp = await client.delete(f"/api/threads/{tid}")
            assert resp.status_code == 200

            # Verify deleted
            resp = await client.get(f"/api/threads/{tid}")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_message_endpoints(self, store):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        app = FastAPI()
        store.mount(app, prefix="/api/threads")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create thread first
            resp = await client.post("/api/threads", json={"title": "Chat"})
            tid = resp.json()["id"]

            # Add message
            resp = await client.post(
                f"/api/threads/{tid}/messages",
                json={"role": "user", "content": "Hello"},
            )
            assert resp.status_code == 201
            assert resp.json()["content"] == "Hello"

            # Get messages
            resp = await client.get(f"/api/threads/{tid}/messages")
            assert resp.status_code == 200
            assert len(resp.json()) == 1

            # Clear messages
            resp = await client.delete(f"/api/threads/{tid}/messages")
            assert resp.status_code == 200

            resp = await client.get(f"/api/threads/{tid}/messages")
            assert len(resp.json()) == 0
