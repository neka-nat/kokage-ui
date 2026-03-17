"""Tests for AI agent components."""

import asyncio
import json

from kokage_ui.ai.agent import (
    AgentEvent,
    AgentMessage,
    AgentView,
    ToolCall,
    agent_stream,
)


class TestToolCall:
    def test_basic(self):
        tc = ToolCall(name="search")
        assert tc.name == "search"
        assert tc.input == ""
        assert tc.result == ""
        assert tc.call_id == ""

    def test_with_all_fields(self):
        tc = ToolCall(
            name="search",
            input={"q": "foo"},
            result="Found 3 items",
            call_id="tc1",
        )
        assert tc.name == "search"
        assert tc.input == {"q": "foo"}
        assert tc.result == "Found 3 items"
        assert tc.call_id == "tc1"


class TestAgentMessage:
    def test_user_message(self):
        msg = AgentMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert msg.name is None

    def test_assistant_with_tools(self):
        tc = ToolCall(name="search", input={"q": "test"}, result="ok", call_id="1")
        msg = AgentMessage(
            role="assistant",
            content="Based on results...",
            tool_calls=[tc],
        )
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "search"

    def test_with_name(self):
        msg = AgentMessage(role="assistant", content="Hi", name="Bot")
        assert msg.name == "Bot"


class TestAgentEvent:
    def test_text_event(self):
        e = AgentEvent(type="text", content="Hello")
        assert e.type == "text"
        assert e.content == "Hello"

    def test_tool_call_event(self):
        e = AgentEvent(
            type="tool_call",
            call_id="tc1",
            tool_name="search",
            tool_input={"q": "foo"},
        )
        assert e.type == "tool_call"
        assert e.tool_name == "search"
        assert e.tool_input == {"q": "foo"}
        assert e.call_id == "tc1"

    def test_tool_result_event(self):
        e = AgentEvent(type="tool_result", call_id="tc1", result="Found items")
        assert e.result == "Found items"

    def test_status_event(self):
        e = AgentEvent(type="status", content="Thinking...")
        assert e.content == "Thinking..."

    def test_error_event(self):
        e = AgentEvent(type="error", content="Something went wrong")
        assert e.content == "Something went wrong"

    def test_done_event(self):
        e = AgentEvent(
            type="done",
            metrics={"tokens": 150, "duration_ms": 2500, "tool_calls": 1},
        )
        assert e.metrics["tokens"] == 150

    def test_to_dict_omits_empty(self):
        e = AgentEvent(type="text", content="Hello")
        d = e.to_dict()
        assert d == {"type": "text", "content": "Hello"}
        assert "tool_name" not in d
        assert "call_id" not in d
        assert "result" not in d
        assert "metrics" not in d

    def test_to_dict_tool_call(self):
        e = AgentEvent(
            type="tool_call",
            call_id="tc1",
            tool_name="search",
            tool_input={"q": "foo"},
        )
        d = e.to_dict()
        assert d == {
            "type": "tool_call",
            "call_id": "tc1",
            "tool_name": "search",
            "tool_input": {"q": "foo"},
        }

    def test_to_dict_done_with_metrics(self):
        e = AgentEvent(type="done", metrics={"tokens": 100})
        d = e.to_dict()
        assert d == {"type": "done", "metrics": {"tokens": 100}}


class TestAgentView:
    def test_render_basic(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        html = str(view)
        assert 'id="test-agent-messages"' in html
        assert 'id="test-agent-form"' in html
        assert 'id="test-agent-input"' in html
        assert 'id="test-agent-btn"' in html

    def test_status_bar_shown(self):
        view = AgentView(
            send_url="/api/agent", show_status=True, agent_id="test-agent"
        )
        html = str(view)
        assert 'id="test-agent-status"' in html

    def test_status_bar_hidden(self):
        view = AgentView(
            send_url="/api/agent", show_status=False, agent_id="test-agent"
        )
        html = str(view)
        assert 'id="test-agent-status"' not in html

    def test_metrics_bar_shown(self):
        view = AgentView(
            send_url="/api/agent", show_metrics=True, agent_id="test-agent"
        )
        html = str(view)
        assert 'id="test-agent-metrics"' in html

    def test_metrics_bar_hidden(self):
        view = AgentView(
            send_url="/api/agent", show_metrics=False, agent_id="test-agent"
        )
        html = str(view)
        assert 'id="test-agent-metrics"' not in html

    def test_initial_messages(self):
        messages = [
            AgentMessage(role="user", content="Hello"),
            AgentMessage(role="assistant", content="Hi there"),
        ]
        view = AgentView(
            send_url="/api/agent", messages=messages, agent_id="test-agent"
        )
        html = str(view)
        assert "Hello" in html
        assert "Hi there" in html
        assert "chat chat-end" in html
        assert "chat chat-start" in html

    def test_tool_collapse_in_initial_messages(self):
        tc = ToolCall(name="search", input={"q": "test"}, result="Found", call_id="1")
        messages = [
            AgentMessage(role="assistant", content="Result:", tool_calls=[tc]),
        ]
        view = AgentView(
            send_url="/api/agent", messages=messages, agent_id="test-agent"
        )
        html = str(view)
        assert "collapse collapse-arrow" in html
        assert "search()" in html
        assert "Found" in html

    def test_xss_escape(self):
        messages = [
            AgentMessage(role="user", content="<script>alert(1)</script>"),
        ]
        view = AgentView(
            send_url="/api/agent", messages=messages, agent_id="test-agent"
        )
        html = str(view)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_custom_parameters(self):
        view = AgentView(
            send_url="/api/agent",
            placeholder="Type here...",
            send_label="Send",
            agent_name="Bot",
            user_name="Alice",
            height="500px",
            agent_id="test-agent",
        )
        html = str(view)
        assert 'placeholder="Type here..."' in html
        assert ">Send</button>" in html
        assert "height:500px" in html

    def test_handle_event_in_script(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        html = str(view)
        assert "handleEvent" in html
        assert "<script>" in html
        assert "</script>" in html

    def test_auto_agent_id(self):
        view = AgentView(send_url="/api/agent")
        html = str(view)
        assert "agent-" in html

    def test_form_elements(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        html = str(view)
        assert 'type="text"' in html
        assert 'type="submit"' in html
        assert "input input-bordered" in html
        assert "btn btn-primary" in html

    def test_send_url_in_js(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        html = str(view)
        assert "/api/agent" in html

    def test_abort_controller_in_script(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        html = str(view)
        assert "AbortController" in html
        assert "abortController.abort()" in html
        assert "AbortError" in html

    def test_stop_button_label_in_js(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        html = str(view)
        assert "stopLabel" in html

    def test_custom_stop_label(self):
        view = AgentView(
            send_url="/api/agent", stop_label="Stop", agent_id="test-agent"
        )
        html = str(view)
        assert '"Stop"' in html

    def test_default_stop_label(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        assert view.stop_label == "停止"

    def test_set_streaming_function_in_script(self):
        view = AgentView(send_url="/api/agent", agent_id="test-agent")
        html = str(view)
        assert "setStreaming" in html
        assert "btn-error" in html

    def test_agent_names_in_bubbles(self):
        messages = [
            AgentMessage(role="user", content="Hi"),
            AgentMessage(role="assistant", content="Hello"),
        ]
        view = AgentView(
            send_url="/api/agent",
            messages=messages,
            user_name="Alice",
            agent_name="Bot",
            agent_id="test-agent",
        )
        html = str(view)
        assert "Alice" in html
        assert "Bot" in html


class TestAgentStream:
    def test_returns_streaming_response(self):
        async def gen():
            yield AgentEvent(type="text", content="hello")

        response = agent_stream(gen())
        assert response.media_type == "text/event-stream"
        assert response.headers["Cache-Control"] == "no-cache"

    def test_sse_format(self):
        async def gen():
            yield AgentEvent(type="text", content="tok1")
            yield AgentEvent(type="text", content="tok2")

        response = agent_stream(gen())

        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        assert len(chunks) == 2

        # Each SSE event must end with \n\n
        for chunk in chunks:
            assert chunk.endswith("\n\n")

        # Check data format
        data1 = json.loads(chunks[0].strip().removeprefix("data: "))
        assert data1["type"] == "text"
        assert data1["content"] == "tok1"

    def test_tool_call_event(self):
        async def gen():
            yield AgentEvent(
                type="tool_call",
                call_id="tc1",
                tool_name="search",
                tool_input={"q": "foo"},
            )

        response = agent_stream(gen())

        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        data = json.loads(chunks[0].strip().removeprefix("data: "))
        assert data["type"] == "tool_call"
        assert data["tool_name"] == "search"
        assert data["tool_input"] == {"q": "foo"}
        assert data["call_id"] == "tc1"

    def test_done_event_with_metrics(self):
        async def gen():
            yield AgentEvent(
                type="done",
                metrics={"tokens": 150, "duration_ms": 2500, "tool_calls": 1},
            )

        response = agent_stream(gen())

        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        data = json.loads(chunks[0].strip().removeprefix("data: "))
        assert data["type"] == "done"
        assert data["metrics"]["tokens"] == 150

    def test_ensure_ascii_false(self):
        async def gen():
            yield AgentEvent(type="text", content="こんにちは")

        response = agent_stream(gen())

        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.get_event_loop().run_until_complete(collect())
        # Japanese text should appear directly, not as \u escapes
        assert "こんにちは" in chunks[0]
