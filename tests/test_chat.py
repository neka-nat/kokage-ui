"""Tests for AI chat components."""

import asyncio
import json

from kokage_ui.ai.chat import ChatMessage, ChatView, chat_stream
from kokage_ui.page import Page


class TestChatMessage:
    def test_basic(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None

    def test_with_name(self):
        msg = ChatMessage(role="assistant", content="Hi", name="Bot")
        assert msg.name == "Bot"


class TestChatView:
    def test_render_basic(self):
        view = ChatView(send_url="/api/chat", chat_id="test-chat")
        html = str(view)
        assert 'id="test-chat-messages"' in html
        assert 'id="test-chat-form"' in html
        assert 'id="test-chat-input"' in html
        assert 'id="test-chat-btn"' in html

    def test_chat_bubble_classes(self):
        messages = [
            ChatMessage(role="user", content="Hi"),
            ChatMessage(role="assistant", content="Hello!"),
        ]
        view = ChatView(send_url="/api/chat", messages=messages, chat_id="test")
        html = str(view)
        assert "chat chat-end" in html
        assert "chat-bubble chat-bubble-primary" in html
        assert "chat chat-start" in html
        assert "chat-bubble prose" in html

    def test_initial_messages_rendered(self):
        messages = [
            ChatMessage(role="user", content="Question"),
            ChatMessage(role="assistant", content="Answer"),
        ]
        view = ChatView(send_url="/api/chat", messages=messages, chat_id="test")
        html = str(view)
        assert "Question" in html
        assert "Answer" in html

    def test_form_elements(self):
        view = ChatView(send_url="/api/chat", chat_id="test")
        html = str(view)
        assert 'type="text"' in html
        assert 'type="submit"' in html
        assert "input input-bordered" in html
        assert "btn btn-primary" in html

    def test_inline_script(self):
        view = ChatView(send_url="/api/chat", chat_id="test")
        html = str(view)
        assert "<script>" in html
        assert "</script>" in html

    def test_send_url_in_js(self):
        view = ChatView(send_url="/api/chat", chat_id="test")
        html = str(view)
        assert "/api/chat" in html

    def test_xss_escape_message(self):
        messages = [ChatMessage(role="user", content="<script>alert(1)</script>")]
        view = ChatView(send_url="/api/chat", messages=messages, chat_id="test")
        html = str(view)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_custom_height(self):
        view = ChatView(send_url="/api/chat", height="400px", chat_id="test")
        html = str(view)
        assert "height:400px" in html

    def test_custom_placeholder(self):
        view = ChatView(
            send_url="/api/chat", placeholder="Type here...", chat_id="test"
        )
        html = str(view)
        assert 'placeholder="Type here..."' in html

    def test_custom_send_label(self):
        view = ChatView(send_url="/api/chat", send_label="Send", chat_id="test")
        html = str(view)
        assert ">Send</button>" in html

    def test_custom_chat_id(self):
        view = ChatView(send_url="/api/chat", chat_id="my-chat")
        html = str(view)
        assert 'id="my-chat-messages"' in html
        assert 'id="my-chat-form"' in html

    def test_auto_chat_id(self):
        view = ChatView(send_url="/api/chat")
        html = str(view)
        assert "chat-" in html

    def test_assistant_and_user_names(self):
        messages = [
            ChatMessage(role="user", content="Hi"),
            ChatMessage(role="assistant", content="Hello"),
        ]
        view = ChatView(
            send_url="/api/chat",
            messages=messages,
            user_name="Alice",
            assistant_name="Bot",
            chat_id="test",
        )
        html = str(view)
        assert "Alice" in html
        assert "Bot" in html

    def test_abort_controller_in_script(self):
        view = ChatView(send_url="/api/chat", chat_id="test")
        html = str(view)
        assert "AbortController" in html
        assert "abortController.abort()" in html
        assert "AbortError" in html

    def test_stop_button_label_in_js(self):
        view = ChatView(send_url="/api/chat", chat_id="test")
        html = str(view)
        assert "stopLabel" in html

    def test_custom_stop_label(self):
        view = ChatView(send_url="/api/chat", stop_label="Stop", chat_id="test")
        html = str(view)
        assert '"Stop"' in html

    def test_default_stop_label(self):
        view = ChatView(send_url="/api/chat", chat_id="test")
        assert view.stop_label == "停止"

    def test_set_streaming_function_in_script(self):
        view = ChatView(send_url="/api/chat", chat_id="test")
        html = str(view)
        assert "setStreaming" in html
        assert "btn-error" in html

    def test_chat_header_in_bubbles(self):
        messages = [ChatMessage(role="assistant", content="Hi")]
        view = ChatView(send_url="/api/chat", messages=messages, chat_id="test")
        html = str(view)
        assert "chat-header" in html


class TestChatStream:
    def test_returns_streaming_response(self):
        async def gen():
            yield "hello"

        response = chat_stream(gen())
        assert response.media_type == "text/event-stream"
        assert response.headers["Cache-Control"] == "no-cache"

    def test_sse_format(self):
        async def gen():
            yield "tok1"
            yield "tok2"

        response = chat_stream(gen())

        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        assert len(chunks) == 3  # tok1, tok2, done

        # Check token events
        data1 = json.loads(chunks[0].strip().removeprefix("data: "))
        assert data1["token"] == "tok1"
        data2 = json.loads(chunks[1].strip().removeprefix("data: "))
        assert data2["token"] == "tok2"

        # Check done event
        done = json.loads(chunks[2].strip().removeprefix("data: "))
        assert done["done"] is True

    def test_sse_newline_format(self):
        async def gen():
            yield "x"

        response = chat_stream(gen())

        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        # Each SSE event must end with \n\n
        for chunk in chunks:
            assert chunk.endswith("\n\n")


class TestPageIncludeMarked:
    def test_include_marked_true(self):
        page = Page(title="Test", include_marked=True)
        html = page.render()
        assert "marked" in html
        assert "marked.min.js" in html

    def test_include_marked_false_by_default(self):
        page = Page(title="Test")
        html = page.render()
        assert "marked.min.js" not in html


class TestAutoDetectDependencies:
    """Page auto-detects ChatView/AgentView and enables marked/highlightjs."""

    def test_chatview_auto_enables_marked(self):
        page = Page(ChatView(send_url="/api/chat"), title="Test")
        html = page.render()
        assert "marked.min.js" in html
        assert "highlight.min.js" in html

    def test_agentview_auto_enables_marked(self):
        from kokage_ui.ai.agent import AgentView

        page = Page(AgentView(send_url="/api/agent"), title="Test")
        html = page.render()
        assert "marked.min.js" in html
        assert "highlight.min.js" in html

    def test_nested_chatview_detected(self):
        from kokage_ui.elements import Div

        page = Page(Div(ChatView(send_url="/api/chat")), title="Test")
        html = page.render()
        assert "marked.min.js" in html

    def test_no_chatview_no_auto_include(self):
        from kokage_ui.elements import Div

        page = Page(Div("hello"), title="Test")
        html = page.render()
        assert "marked.min.js" not in html

    def test_explicit_false_is_overridden_by_auto_detect(self):
        """Auto-detect enables dependencies even if not explicitly set."""
        page = Page(ChatView(send_url="/api/chat"), title="Test")
        assert page.include_marked is True
        assert page.include_highlightjs is True
