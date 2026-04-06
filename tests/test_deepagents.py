"""Tests for Deep Agents stream adapter."""

import json
import sys
from types import ModuleType

import pytest

from kokage_ui.ai.agent import AgentEvent

# ---------- Mock langchain_core.messages ----------
# When running as part of the full test suite, test_langchain.py may install
# its own mock classes into sys.modules. We must always use the classes from
# sys.modules at construction time so isinstance checks in the adapter match.
# We achieve this by using factory helpers instead of capturing classes at
# module-level.


def _ensure_mock_langchain():
    """Install mock langchain_core into sys.modules if not already present."""
    if "langchain_core.messages" in sys.modules:
        return

    class _AIMessageChunk:
        def __init__(self, content="", tool_calls=None, tool_call_chunks=None):
            self.content = content
            self.tool_calls = tool_calls or []
            self.tool_call_chunks = tool_call_chunks or []

    class _ToolMessage:
        def __init__(self, content="", tool_call_id=""):
            self.content = content
            self.tool_call_id = tool_call_id

    class _AIMessage:
        def __init__(self, content="", tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls or []

    messages_mod = ModuleType("langchain_core.messages")
    messages_mod.AIMessageChunk = _AIMessageChunk
    messages_mod.ToolMessage = _ToolMessage
    messages_mod.AIMessage = _AIMessage

    core_mod = ModuleType("langchain_core")
    core_mod.messages = messages_mod

    sys.modules["langchain_core"] = core_mod
    sys.modules["langchain_core.messages"] = messages_mod


_ensure_mock_langchain()


def _ensure_mock_langgraph():
    """Install mock langgraph.types if not present."""
    if "langgraph.types" in sys.modules:
        return

    class _Command:
        def __init__(self, *, resume=None):
            self.resume = resume

    types_mod = ModuleType("langgraph.types")
    types_mod.Command = _Command

    lg_mod = ModuleType("langgraph")
    lg_mod.types = types_mod

    sys.modules.setdefault("langgraph", lg_mod)
    sys.modules["langgraph.types"] = types_mod


_ensure_mock_langgraph()


def _MockAIMessageChunk(content="", tool_calls=None, tool_call_chunks=None):
    """Create an AIMessageChunk using the class currently in sys.modules."""
    cls = sys.modules["langchain_core.messages"].AIMessageChunk
    return cls(content=content, tool_calls=tool_calls, tool_call_chunks=tool_call_chunks)


def _MockToolMessage(content="", tool_call_id=""):
    """Create a ToolMessage using the class currently in sys.modules."""
    cls = sys.modules["langchain_core.messages"].ToolMessage
    return cls(content=content, tool_call_id=tool_call_id)


def _MockAIMessage(content="", tool_calls=None):
    """Create an AIMessage using the class currently in sys.modules."""
    cls = sys.modules["langchain_core.messages"].AIMessage
    return cls(content=content, tool_calls=tool_calls)


from kokage_ui.ai.deepagents import (  # noqa: E402
    DeepAgentConfig,
    _deep_agent_events,
    _deep_agent_resume_events,
    _detect_result_hint,
    _guess_preview_hint,
    _handle_messages,
    _handle_updates,
    deep_agent_stream,
    deep_agent_resume,
    to_deep_agent_tools,
)


# ---------- Helpers ----------


async def _async_iter(items):
    for item in items:
        yield item


async def _collect(ait):
    return [e async for e in ait]


# ==================== Preview Hint Detection ====================


class TestPreviewHints:
    def test_guess_hint_from_python_path(self):
        assert _guess_preview_hint("read_file", {"path": "main.py"}) == "python"

    def test_guess_hint_from_json_path(self):
        assert _guess_preview_hint("read_file", {"path": "data.json"}) == "json"

    def test_guess_hint_from_toml_path(self):
        assert _guess_preview_hint("write_file", {"path": "pyproject.toml"}) == "toml"

    def test_guess_hint_from_image_path(self):
        assert _guess_preview_hint("read_file", {"path": "logo.png"}) == "image"

    def test_guess_hint_non_filesystem_tool(self):
        assert _guess_preview_hint("search", {"path": "data.json"}) == ""

    def test_guess_hint_no_path(self):
        assert _guess_preview_hint("read_file", {"content": "hello"}) == ""

    def test_guess_hint_string_input(self):
        assert _guess_preview_hint("read_file", "config.yaml") == "yaml"

    def test_guess_hint_unknown_extension(self):
        assert _guess_preview_hint("read_file", {"path": "data.xyz"}) == ""

    def test_detect_result_json_object(self):
        assert _detect_result_hint('{"key": "value"}', "search") == "json"

    def test_detect_result_json_array(self):
        assert _detect_result_hint('[1, 2, 3]', "search") == "json"

    def test_detect_result_invalid_json(self):
        assert _detect_result_hint("{not json", "search") == ""

    def test_detect_result_empty(self):
        assert _detect_result_hint("", "search") == ""

    def test_detect_result_ls_tool(self):
        """ls results should not get json hint even if they look like JSON."""
        assert _detect_result_hint("file1\nfile2", "ls") == ""


# ==================== Messages Mode ====================


class TestHandleMessages:
    @pytest.mark.asyncio
    async def test_text_streaming(self):
        items = [
            (_MockAIMessageChunk(content="Hello"), {"langgraph_node": "agent"}),
            (_MockAIMessageChunk(content=" world"), {"langgraph_node": "agent"}),
        ]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        text_events = [e for e in result if e.type == "text"]
        assert len(text_events) == 2
        assert text_events[0].content == "Hello"
        assert text_events[1].content == " world"

    @pytest.mark.asyncio
    async def test_tool_call_and_result(self):
        items = [
            (
                _MockAIMessageChunk(
                    tool_calls=[{"id": "tc1", "name": "read_file", "args": {"path": "app.py"}}]
                ),
                {"langgraph_node": "agent"},
            ),
            (
                _MockToolMessage(content="import fastapi", tool_call_id="tc1"),
                {"langgraph_node": "tools"},
            ),
        ]
        config = DeepAgentConfig()
        tool_inputs: dict = {}
        tool_names: dict = {}
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs=tool_inputs,
                tool_names=tool_names,
                state={},
            )
        )
        tc_events = [e for e in result if e.type == "tool_call"]
        tr_events = [e for e in result if e.type == "tool_result"]
        assert len(tc_events) == 1
        assert tc_events[0].tool_name == "read_file"
        assert tc_events[0].tool_input == {"path": "app.py"}
        assert len(tr_events) == 1
        assert tr_events[0].result == "import fastapi"
        assert tr_events[0].preview_hint == "python"

    @pytest.mark.asyncio
    async def test_tool_call_dedup(self):
        chunk = _MockAIMessageChunk(
            tool_calls=[{"id": "tc1", "name": "search", "args": {}}]
        )
        items = [
            (chunk, {"langgraph_node": "agent"}),
            (chunk, {"langgraph_node": "agent"}),
        ]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        tc_events = [e for e in result if e.type == "tool_call"]
        assert len(tc_events) == 1

    @pytest.mark.asyncio
    async def test_node_status_events(self):
        items = [
            (_MockAIMessageChunk(content="hi"), {"langgraph_node": "agent"}),
            (_MockToolMessage(content="r", tool_call_id="tc1"), {"langgraph_node": "tools"}),
        ]
        config = DeepAgentConfig(include_status=True)
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        status_events = [e for e in result if e.type == "status"]
        assert len(status_events) == 2
        assert "agent" in status_events[0].content
        assert "tools" in status_events[1].content

    @pytest.mark.asyncio
    async def test_no_status_when_disabled(self):
        items = [
            (_MockAIMessageChunk(content="hi"), {"langgraph_node": "agent"}),
        ]
        config = DeepAgentConfig(include_status=False)
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        status_events = [e for e in result if e.type == "status"]
        assert len(status_events) == 0

    @pytest.mark.asyncio
    async def test_write_todos_plan_event(self):
        items = [
            (
                _MockAIMessageChunk(
                    tool_calls=[{"id": "tc1", "name": "write_todos", "args": {"todos": "plan"}}]
                ),
                {"langgraph_node": "agent"},
            ),
            (
                _MockToolMessage(content='[{"task":"step1"}]', tool_call_id="tc1"),
                {"langgraph_node": "tools"},
            ),
        ]
        config = DeepAgentConfig(include_plan=True)
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        plan_events = [e for e in result if e.type == "status" and "Plan" in e.content]
        assert len(plan_events) == 1

    @pytest.mark.asyncio
    async def test_no_plan_event_when_disabled(self):
        items = [
            (
                _MockAIMessageChunk(
                    tool_calls=[{"id": "tc1", "name": "write_todos", "args": {}}]
                ),
                {"langgraph_node": "agent"},
            ),
            (
                _MockToolMessage(content="[]", tool_call_id="tc1"),
                {"langgraph_node": "tools"},
            ),
        ]
        config = DeepAgentConfig(include_plan=False)
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        plan_events = [e for e in result if e.type == "status" and "Plan" in e.content]
        assert len(plan_events) == 0

    @pytest.mark.asyncio
    async def test_dict_tool_result_serialized(self):
        items = [
            (
                _MockToolMessage(content={"key": "val"}, tool_call_id="tc1"),
                {"langgraph_node": "tools"},
            ),
        ]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        tr = [e for e in result if e.type == "tool_result"][0]
        assert tr.result == '{"key": "val"}'

    @pytest.mark.asyncio
    async def test_json_result_auto_hint(self):
        """JSON tool results should get auto-detected preview hint."""
        items = [
            (
                _MockAIMessageChunk(
                    tool_calls=[{"id": "tc1", "name": "search", "args": {"q": "test"}}]
                ),
                {"langgraph_node": "agent"},
            ),
            (
                _MockToolMessage(content='[{"name": "result"}]', tool_call_id="tc1"),
                {"langgraph_node": "tools"},
            ),
        ]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        tr = [e for e in result if e.type == "tool_result"][0]
        assert tr.preview_hint == "json"

    @pytest.mark.asyncio
    async def test_tool_call_chunks_streaming(self):
        items = [
            (
                _MockAIMessageChunk(
                    tool_call_chunks=[{"id": "tc1", "name": "search", "args": ""}]
                ),
                {"langgraph_node": "agent"},
            ),
        ]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_messages(
                _async_iter(items),
                config=config,
                tool_calls_seen=set(),
                tool_inputs={},
                tool_names={},
                state={},
            )
        )
        tc_events = [e for e in result if e.type == "tool_call"]
        assert len(tc_events) == 1
        assert tc_events[0].tool_name == "search"


# ==================== Updates Mode ====================


class TestHandleUpdates:
    @pytest.mark.asyncio
    async def test_text_from_ai_message(self):
        updates = [
            {"agent": {"messages": [_MockAIMessage(content="Hello")]}}
        ]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_updates(
                _async_iter(updates),
                config=config,
                tool_inputs={},
                tool_names={},
            )
        )
        text_events = [e for e in result if e.type == "text"]
        assert len(text_events) == 1
        assert text_events[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_tool_call_from_ai_message(self):
        msg = _MockAIMessage(
            tool_calls=[{"id": "tc1", "name": "read_file", "args": {"path": "main.py"}}],
        )
        updates = [{"agent": {"messages": [msg]}}]
        config = DeepAgentConfig()
        tool_inputs: dict = {}
        tool_names: dict = {}
        result = await _collect(
            _handle_updates(
                _async_iter(updates),
                config=config,
                tool_inputs=tool_inputs,
                tool_names=tool_names,
            )
        )
        tc_events = [e for e in result if e.type == "tool_call"]
        assert len(tc_events) == 1
        assert tc_events[0].tool_name == "read_file"
        assert tool_names["tc1"] == "read_file"

    @pytest.mark.asyncio
    async def test_tool_result_with_preview_hint(self):
        tool_inputs = {"tc1": {"path": "data.json"}}
        tool_names = {"tc1": "read_file"}
        updates = [
            {"tools": {"messages": [_MockToolMessage(content='{"a":1}', tool_call_id="tc1")]}}
        ]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_updates(
                _async_iter(updates),
                config=config,
                tool_inputs=tool_inputs,
                tool_names=tool_names,
            )
        )
        tr = [e for e in result if e.type == "tool_result"][0]
        assert tr.preview_hint == "json"

    @pytest.mark.asyncio
    async def test_node_status(self):
        updates = [
            {"agent": {"messages": [_MockAIMessage(content="hi")]}},
            {"tools": {"messages": [_MockToolMessage(content="r", tool_call_id="tc1")]}},
        ]
        config = DeepAgentConfig(include_status=True)
        result = await _collect(
            _handle_updates(
                _async_iter(updates),
                config=config,
                tool_inputs={},
                tool_names={},
            )
        )
        status_events = [e for e in result if e.type == "status"]
        assert any("agent" in e.content for e in status_events)
        assert any("tools" in e.content for e in status_events)

    @pytest.mark.asyncio
    async def test_done_not_emitted_by_handler(self):
        """_handle_updates should NOT emit done — that's _deep_agent_events' job."""
        updates = [{"agent": {"messages": []}}]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_updates(
                _async_iter(updates),
                config=config,
                tool_inputs={},
                tool_names={},
            )
        )
        done_events = [e for e in result if e.type == "done"]
        assert len(done_events) == 0

    @pytest.mark.asyncio
    async def test_non_dict_update_skipped(self):
        updates = ["not a dict", {"agent": {"messages": [_MockAIMessage(content="ok")]}}]
        config = DeepAgentConfig()
        result = await _collect(
            _handle_updates(
                _async_iter(updates),
                config=config,
                tool_inputs={},
                tool_names={},
            )
        )
        text_events = [e for e in result if e.type == "text"]
        assert len(text_events) == 1


# ==================== Mock Agent for deep_agent_events ====================


class _MockInterrupt:
    """Mock LangGraph Interrupt object."""

    def __init__(self, value):
        self.value = value


class _MockTask:
    """Mock LangGraph task with optional interrupts."""

    def __init__(self, interrupts=None):
        self.interrupts = interrupts or []


class _MockState:
    """Mock LangGraph graph state."""

    def __init__(self, next_nodes=None, tasks=None):
        self.next = next_nodes or ()
        self.tasks = tasks or ()


class _MockCompiledGraph:
    """Mock compiled graph that simulates Deep Agent astream."""

    def __init__(self, events, state=None):
        self._events = events
        self._state = state

    async def astream(self, input_data, *, config=None, stream_mode="messages"):
        for item in self._events:
            yield item

    def get_state(self, config=None):
        return self._state or _MockState()


class TestDeepAgentEvents:
    @pytest.mark.asyncio
    async def test_full_flow(self):
        """End-to-end: status → tool_call → tool_result → text → done."""
        events = [
            (
                _MockAIMessageChunk(
                    tool_calls=[{"id": "tc1", "name": "search", "args": {"q": "hi"}}]
                ),
                {"langgraph_node": "agent"},
            ),
            (
                _MockToolMessage(content="found it", tool_call_id="tc1"),
                {"langgraph_node": "tools"},
            ),
            (_MockAIMessageChunk(content="Answer"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        result = await _collect(
            _deep_agent_events(mock_agent, "hello", config=DeepAgentConfig())
        )
        types = [e.type for e in result]
        assert "status" in types
        assert "tool_call" in types
        assert "tool_result" in types
        assert "text" in types
        assert types[-1] == "done"

    @pytest.mark.asyncio
    async def test_metrics_in_done(self):
        events = [
            (_MockAIMessageChunk(content="hi"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        result = await _collect(
            _deep_agent_events(mock_agent, "test", config=DeepAgentConfig(include_metrics=True))
        )
        done = [e for e in result if e.type == "done"][0]
        assert done.metrics is not None
        assert "duration_ms" in done.metrics
        assert done.metrics["tool_calls"] == 0

    @pytest.mark.asyncio
    async def test_no_metrics_when_disabled(self):
        events = [
            (_MockAIMessageChunk(content="hi"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        result = await _collect(
            _deep_agent_events(mock_agent, "test", config=DeepAgentConfig(include_metrics=False))
        )
        done = [e for e in result if e.type == "done"][0]
        assert done.metrics is None

    @pytest.mark.asyncio
    async def test_thread_id_passed_in_config(self):
        """Verify thread_id is forwarded to LangGraph config."""
        captured_config = {}

        class _CapturingGraph:
            async def astream(self, input_data, *, config=None, stream_mode="messages"):
                captured_config.update(config or {})
                return
                yield  # make it an async generator

        agent = _CapturingGraph()
        await _collect(
            _deep_agent_events(agent, "hi", thread_id="t123", config=DeepAgentConfig())
        )
        assert captured_config.get("configurable", {}).get("thread_id") == "t123"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Errors during streaming should produce error event then done."""

        class _ErrorGraph:
            async def astream(self, input_data, *, config=None, stream_mode="messages"):
                raise RuntimeError("LLM connection failed")
                yield  # noqa: unreachable

        agent = _ErrorGraph()
        result = await _collect(
            _deep_agent_events(agent, "test", config=DeepAgentConfig())
        )
        error_events = [e for e in result if e.type == "error"]
        assert len(error_events) == 1
        assert "LLM connection failed" in error_events[0].content
        assert result[-1].type == "done"

    @pytest.mark.asyncio
    async def test_updates_mode(self):
        events = [
            {"agent": {"messages": [_MockAIMessage(content="Hello from updates")]}}
        ]
        mock_agent = _MockCompiledGraph(events)
        config = DeepAgentConfig(stream_mode="updates")
        result = await _collect(
            _deep_agent_events(mock_agent, "test", config=config)
        )
        text_events = [e for e in result if e.type == "text"]
        assert len(text_events) == 1
        assert text_events[0].content == "Hello from updates"

    @pytest.mark.asyncio
    async def test_tool_call_count_in_metrics(self):
        events = [
            (
                _MockAIMessageChunk(
                    tool_calls=[{"id": "tc1", "name": "search", "args": {}}]
                ),
                {"langgraph_node": "agent"},
            ),
            (_MockToolMessage(content="r", tool_call_id="tc1"), {"langgraph_node": "tools"}),
            (
                _MockAIMessageChunk(
                    tool_calls=[{"id": "tc2", "name": "read_file", "args": {"path": "a.py"}}]
                ),
                {"langgraph_node": "agent"},
            ),
            (_MockToolMessage(content="code", tool_call_id="tc2"), {"langgraph_node": "tools"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        result = await _collect(
            _deep_agent_events(mock_agent, "test", config=DeepAgentConfig())
        )
        done = [e for e in result if e.type == "done"][0]
        assert done.metrics["tool_calls"] == 2


# ==================== deep_agent_stream ====================


class TestDeepAgentStream:
    def test_returns_streaming_response(self):
        from starlette.responses import StreamingResponse

        events = [
            (_MockAIMessageChunk(content="Hi"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        resp = deep_agent_stream(mock_agent, "hello")
        assert isinstance(resp, StreamingResponse)
        assert resp.media_type == "text/event-stream"

    def test_with_config(self):
        from starlette.responses import StreamingResponse

        events = [
            (_MockAIMessageChunk(content="Hi"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        config = DeepAgentConfig(include_status=False, include_metrics=False)
        resp = deep_agent_stream(mock_agent, "hello", config=config)
        assert isinstance(resp, StreamingResponse)


# ==================== to_deep_agent_tools ====================


class TestToDeepAgentTools:
    def test_from_registry(self):
        from kokage_ui.ai.tools import ToolRegistry

        reg = ToolRegistry()

        @reg.tool
        def search(query: str) -> str:
            """Search."""
            return query

        @reg.tool
        async def fetch(url: str) -> str:
            """Fetch."""
            return url

        tools = to_deep_agent_tools(reg)
        assert len(tools) == 2
        assert callable(tools[0])
        assert callable(tools[1])
        assert tools[0].__name__ == "search"
        assert tools[1].__name__ == "fetch"

    def test_from_tool_info_list(self):
        from kokage_ui.ai.tools import ToolInfo

        def my_fn(x: str) -> str:
            return x

        infos = [ToolInfo(name="test", description="A test", parameters={}, func=my_fn)]
        tools = to_deep_agent_tools(infos)
        assert len(tools) == 1
        assert tools[0] is my_fn

    def test_invalid_source_raises(self):
        with pytest.raises(TypeError, match="Expected ToolRegistry"):
            to_deep_agent_tools("not valid")

    def test_empty_registry(self):
        from kokage_ui.ai.tools import ToolRegistry

        reg = ToolRegistry()
        tools = to_deep_agent_tools(reg)
        assert tools == []


# ==================== DeepAgentConfig ====================


class TestDeepAgentConfig:
    def test_defaults(self):
        config = DeepAgentConfig()
        assert config.include_status is True
        assert config.include_plan is True
        assert config.include_metrics is True
        assert config.stream_mode == "messages"

    def test_custom(self):
        config = DeepAgentConfig(
            include_status=False,
            include_plan=False,
            include_metrics=False,
            stream_mode="updates",
        )
        assert config.include_status is False
        assert config.stream_mode == "updates"


# ==================== Interrupt Detection ====================


class TestCheckInterrupt:
    def test_no_interrupt_returns_none(self):
        from kokage_ui.ai.deepagents import _check_interrupt

        agent = _MockCompiledGraph([], state=_MockState())
        result = _check_interrupt(agent, {})
        assert result is None

    def test_detects_hitl_interrupt(self):
        from kokage_ui.ai.deepagents import _check_interrupt

        interrupt_value = {
            "action_requests": [{"name": "delete_file", "args": {"path": "/tmp/x"}}],
            "review_configs": [{"action_name": "delete_file", "allowed_decisions": ["approve", "reject"]}],
        }
        state = _MockState(
            tasks=[_MockTask(interrupts=[_MockInterrupt(interrupt_value)])]
        )
        agent = _MockCompiledGraph([], state=state)
        result = _check_interrupt(agent, {})
        assert result is not None
        assert result["action_requests"][0]["name"] == "delete_file"

    def test_detects_generic_interrupt_via_next(self):
        from kokage_ui.ai.deepagents import _check_interrupt

        state = _MockState(next_nodes=("tools",))
        agent = _MockCompiledGraph([], state=state)
        result = _check_interrupt(agent, {})
        assert result is not None
        assert result["action_requests"] == []

    def test_no_get_state_returns_none(self):
        from kokage_ui.ai.deepagents import _check_interrupt

        class _NoState:
            pass

        result = _check_interrupt(_NoState(), {})
        assert result is None

    def test_get_state_exception_returns_none(self):
        from kokage_ui.ai.deepagents import _check_interrupt

        class _ErrorState:
            def get_state(self, config):
                raise RuntimeError("bad state")

        result = _check_interrupt(_ErrorState(), {})
        assert result is None


class TestInterruptToEvent:
    def test_single_action(self):
        from kokage_ui.ai.deepagents import _interrupt_to_event

        info = {
            "action_requests": [{"name": "execute", "args": {"command": "rm -rf /"}}],
            "review_configs": [{"action_name": "execute", "allowed_decisions": ["approve", "reject"]}],
        }
        event = _interrupt_to_event(info, thread_id="t1")
        assert event.type == "interrupt"
        assert "execute" in event.content
        assert event.tool_name == "execute"
        assert event.tool_input == {"command": "rm -rf /"}
        assert event.metrics["thread_id"] == "t1"
        assert len(event.metrics["action_requests"]) == 1

    def test_multiple_actions(self):
        from kokage_ui.ai.deepagents import _interrupt_to_event

        info = {
            "action_requests": [
                {"name": "delete_file", "args": {"path": "a.txt"}},
                {"name": "send_email", "args": {"to": "x@y.com"}},
            ],
            "review_configs": [],
        }
        event = _interrupt_to_event(info, thread_id="t2")
        assert "delete_file" in event.content
        assert "send_email" in event.content
        assert event.tool_name == "delete_file"  # first tool
        assert len(event.metrics["action_requests"]) == 2

    def test_empty_actions(self):
        from kokage_ui.ai.deepagents import _interrupt_to_event

        info = {"action_requests": [], "review_configs": []}
        event = _interrupt_to_event(info, thread_id=None)
        assert event.type == "interrupt"
        assert event.metrics["thread_id"] is None


# ==================== Interrupt in deep_agent_events ====================


class TestDeepAgentInterrupt:
    @pytest.mark.asyncio
    async def test_interrupt_emitted_instead_of_done(self):
        """When agent is interrupted, emit interrupt event, not done."""
        events = [
            (_MockAIMessageChunk(content="Thinking..."), {"langgraph_node": "agent"}),
        ]
        interrupt_value = {
            "action_requests": [{"name": "delete_file", "args": {"path": "x"}}],
            "review_configs": [],
        }
        state = _MockState(
            tasks=[_MockTask(interrupts=[_MockInterrupt(interrupt_value)])]
        )
        mock_agent = _MockCompiledGraph(events, state=state)
        result = await _collect(
            _deep_agent_events(mock_agent, "delete x", thread_id="t1", config=DeepAgentConfig())
        )
        types = [e.type for e in result]
        assert "interrupt" in types
        assert "done" not in types
        interrupt_event = [e for e in result if e.type == "interrupt"][0]
        assert interrupt_event.tool_name == "delete_file"
        assert interrupt_event.metrics["thread_id"] == "t1"

    @pytest.mark.asyncio
    async def test_no_interrupt_emits_done(self):
        """Normal completion should emit done, not interrupt."""
        events = [
            (_MockAIMessageChunk(content="Done"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events, state=_MockState())
        result = await _collect(
            _deep_agent_events(mock_agent, "hi", config=DeepAgentConfig())
        )
        types = [e.type for e in result]
        assert "done" in types
        assert "interrupt" not in types

    @pytest.mark.asyncio
    async def test_interrupt_without_thread_id(self):
        events = []
        state = _MockState(next_nodes=("tools",))
        mock_agent = _MockCompiledGraph(events, state=state)
        result = await _collect(
            _deep_agent_events(mock_agent, "test", config=DeepAgentConfig())
        )
        interrupt_events = [e for e in result if e.type == "interrupt"]
        assert len(interrupt_events) == 1
        assert interrupt_events[0].metrics["thread_id"] is None


# ==================== deep_agent_resume ====================


class TestDeepAgentResume:
    def test_returns_streaming_response(self):
        from starlette.responses import StreamingResponse
        from kokage_ui.ai.deepagents import deep_agent_resume

        events = [
            (_MockAIMessageChunk(content="Resumed"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        resp = deep_agent_resume(
            mock_agent,
            decisions=[{"type": "approve"}],
            thread_id="t1",
        )
        assert isinstance(resp, StreamingResponse)
        assert resp.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_resume_approve_flow(self):
        from kokage_ui.ai.deepagents import _deep_agent_resume_events

        events = [
            (_MockToolMessage(content="File deleted", tool_call_id="tc1"), {"langgraph_node": "tools"}),
            (_MockAIMessageChunk(content="Done!"), {"langgraph_node": "agent"}),
        ]
        mock_agent = _MockCompiledGraph(events)
        result = await _collect(
            _deep_agent_resume_events(
                mock_agent,
                decisions=[{"type": "approve"}],
                thread_id="t1",
                config=DeepAgentConfig(),
            )
        )
        types = [e.type for e in result]
        assert "tool_result" in types
        assert "text" in types
        assert types[-1] == "done"

    @pytest.mark.asyncio
    async def test_resume_chained_interrupt(self):
        """If another interrupt occurs after resume, emit interrupt again."""
        from kokage_ui.ai.deepagents import _deep_agent_resume_events

        events = [
            (_MockToolMessage(content="ok", tool_call_id="tc1"), {"langgraph_node": "tools"}),
        ]
        interrupt_value = {
            "action_requests": [{"name": "execute", "args": {"command": "ls"}}],
            "review_configs": [],
        }
        state = _MockState(
            tasks=[_MockTask(interrupts=[_MockInterrupt(interrupt_value)])]
        )
        mock_agent = _MockCompiledGraph(events, state=state)
        result = await _collect(
            _deep_agent_resume_events(
                mock_agent,
                decisions=[{"type": "approve"}],
                thread_id="t1",
                config=DeepAgentConfig(),
            )
        )
        types = [e.type for e in result]
        assert "interrupt" in types
        assert "done" not in types

    @pytest.mark.asyncio
    async def test_resume_error(self):
        from kokage_ui.ai.deepagents import _deep_agent_resume_events

        class _ErrorGraph:
            async def astream(self, input_data, *, config=None, stream_mode="messages"):
                raise RuntimeError("resume failed")
                yield

            def get_state(self, config=None):
                return _MockState()

        result = await _collect(
            _deep_agent_resume_events(
                _ErrorGraph(),
                decisions=[{"type": "approve"}],
                thread_id="t1",
                config=DeepAgentConfig(),
            )
        )
        error_events = [e for e in result if e.type == "error"]
        assert len(error_events) == 1
        assert result[-1].type == "done"


# ==================== AgentView interrupt_url ====================


class TestAgentViewInterrupt:
    def test_interrupt_url_rendered(self):
        from kokage_ui.ai.agent import AgentView

        view = AgentView(send_url="/api/agent", interrupt_url="/api/resume")
        html = view.render()
        assert '"/api/resume"' in html
        assert "interruptUrl" in html
        assert "showInterruptModal" in html

    def test_no_interrupt_url(self):
        from kokage_ui.ai.agent import AgentView

        view = AgentView(send_url="/api/agent")
        html = view.render()
        assert "interruptUrl = null" in html

    def test_custom_labels(self):
        from kokage_ui.ai.agent import AgentView

        view = AgentView(
            send_url="/api/agent",
            interrupt_url="/api/resume",
            approve_label="Allow",
            reject_label="Deny",
        )
        html = view.render()
        assert '"Allow"' in html
        assert '"Deny"' in html
