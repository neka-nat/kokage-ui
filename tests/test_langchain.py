"""Tests for LangChain and LangGraph stream adapters."""

import json
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from kokage_ui.ai.agent import AgentEvent

# ---------- Mock langchain_core.messages ----------


class _MockAIMessageChunk:
    def __init__(self, content="", tool_calls=None, tool_call_chunks=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.tool_call_chunks = tool_call_chunks or []


class _MockToolMessage:
    def __init__(self, content="", tool_call_id=""):
        self.content = content
        self.tool_call_id = tool_call_id


class _MockAIMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class _MockAsyncCallbackHandler:
    """Mock base class for AsyncCallbackHandler."""
    pass


class _MockStructuredTool:
    """Mock StructuredTool returned by from_function."""

    def __init__(self, *, func=None, coroutine=None, name="", description="", handle_tool_error=True):
        self.func = func
        self.coroutine = coroutine
        self.name = name
        self.description = description
        self.handle_tool_error = handle_tool_error

    @classmethod
    def from_function(cls, *, func=None, coroutine=None, name="", description="", handle_tool_error=True):
        return cls(func=func, coroutine=coroutine, name=name, description=description, handle_tool_error=handle_tool_error)


def _install_mock_langchain():
    """Install mock langchain_core into sys.modules."""
    messages_mod = ModuleType("langchain_core.messages")
    messages_mod.AIMessageChunk = _MockAIMessageChunk
    messages_mod.ToolMessage = _MockToolMessage
    messages_mod.AIMessage = _MockAIMessage

    callbacks_mod = ModuleType("langchain_core.callbacks")
    callbacks_mod.AsyncCallbackHandler = _MockAsyncCallbackHandler

    tools_mod = ModuleType("langchain_core.tools")
    tools_mod.StructuredTool = _MockStructuredTool

    core_mod = ModuleType("langchain_core")
    core_mod.messages = messages_mod
    core_mod.callbacks = callbacks_mod
    core_mod.tools = tools_mod

    sys.modules["langchain_core"] = core_mod
    sys.modules["langchain_core.messages"] = messages_mod
    sys.modules["langchain_core.callbacks"] = callbacks_mod
    sys.modules["langchain_core.tools"] = tools_mod


_install_mock_langchain()

from kokage_ui.ai.langchain import LangChainCallbackHandler, langchain_stream, to_langchain_tools  # noqa: E402
from kokage_ui.ai.langgraph import langgraph_stream  # noqa: E402
from kokage_ui.ai.tools import ToolRegistry  # noqa: E402


# ---------- Helpers ----------


async def _async_iter(items):
    for item in items:
        yield item


async def _collect(ait):
    return [e async for e in ait]


# ==================== langchain_stream ====================


class TestLangchainStream:
    @pytest.mark.asyncio
    async def test_text_streaming(self):
        events = [
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": _MockAIMessageChunk(content="Hello")},
                "run_id": "r1",
            },
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": _MockAIMessageChunk(content=" world")},
                "run_id": "r1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert len(result) == 2
        assert result[0] == AgentEvent(type="text", content="Hello")
        assert result[1] == AgentEvent(type="text", content=" world")

    @pytest.mark.asyncio
    async def test_tool_call_via_on_tool_start(self):
        events = [
            {
                "event": "on_tool_start",
                "name": "search",
                "data": {"input": {"query": "test"}},
                "run_id": "tc1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        tool_events = [e for e in result if e.type == "tool_call"]
        assert len(tool_events) == 1
        assert tool_events[0].tool_name == "search"
        assert tool_events[0].tool_input == {"query": "test"}
        assert tool_events[0].call_id == "tc1"

    @pytest.mark.asyncio
    async def test_tool_result_via_on_tool_end(self):
        events = [
            {
                "event": "on_tool_end",
                "data": {"output": _MockToolMessage(content="Found 3 items", tool_call_id="tc1")},
                "run_id": "tc1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert len(result) == 1
        assert result[0].type == "tool_result"
        assert result[0].result == "Found 3 items"
        assert result[0].call_id == "tc1"

    @pytest.mark.asyncio
    async def test_tool_end_string_output(self):
        events = [
            {
                "event": "on_tool_end",
                "data": {"output": "plain result"},
                "run_id": "tc1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert result[0].result == "plain result"

    @pytest.mark.asyncio
    async def test_tool_end_dict_output(self):
        events = [
            {
                "event": "on_tool_end",
                "data": {"output": {"key": "value"}},
                "run_id": "tc1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert result[0].result == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_status_on_agent_chain_start(self):
        events = [
            {
                "event": "on_chain_start",
                "name": "AgentExecutor",
                "data": {},
                "run_id": "r1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert len(result) == 1
        assert result[0].type == "status"
        assert result[0].content == "Thinking..."

    @pytest.mark.asyncio
    async def test_no_status_when_disabled(self):
        events = [
            {
                "event": "on_chain_start",
                "name": "AgentExecutor",
                "data": {},
                "run_id": "r1",
            },
            {
                "event": "on_tool_start",
                "name": "search",
                "data": {"input": "q"},
                "run_id": "tc1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events), include_status=False))
        status_events = [e for e in result if e.type == "status"]
        assert len(status_events) == 0

    @pytest.mark.asyncio
    async def test_done_on_agent_chain_end(self):
        events = [
            {
                "event": "on_chain_end",
                "name": "AgentExecutor",
                "data": {},
                "run_id": "r1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert len(result) == 1
        assert result[0].type == "done"

    @pytest.mark.asyncio
    async def test_non_agent_chain_ignored(self):
        events = [
            {
                "event": "on_chain_start",
                "name": "RunnableSequence",
                "data": {},
                "run_id": "r1",
            },
            {
                "event": "on_chain_end",
                "name": "RunnableSequence",
                "data": {},
                "run_id": "r1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_empty_content_skipped(self):
        events = [
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": _MockAIMessageChunk(content="")},
                "run_id": "r1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_tool_call_dedup(self):
        """Same tool call ID should not produce duplicate events."""
        events = [
            {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": _MockAIMessageChunk(
                        tool_call_chunks=[{"id": "tc1", "name": "search", "args": ""}]
                    )
                },
                "run_id": "r1",
            },
            {
                "event": "on_tool_start",
                "name": "search",
                "data": {"input": {"q": "test"}},
                "run_id": "tc1",
            },
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        tool_calls = [e for e in result if e.type == "tool_call"]
        assert len(tool_calls) == 1

    @pytest.mark.asyncio
    async def test_full_flow(self):
        """End-to-end: status → tool_call → tool_result → text → done."""
        events = [
            {"event": "on_chain_start", "name": "Agent", "data": {}, "run_id": "r1"},
            {"event": "on_tool_start", "name": "search", "data": {"input": {"q": "hello"}}, "run_id": "tc1"},
            {
                "event": "on_tool_end",
                "data": {"output": _MockToolMessage(content="result", tool_call_id="tc1")},
                "run_id": "tc1",
            },
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": _MockAIMessageChunk(content="Answer")},
                "run_id": "r2",
            },
            {"event": "on_chain_end", "name": "Agent", "data": {}, "run_id": "r1"},
        ]
        result = await _collect(langchain_stream(_async_iter(events)))
        types = [e.type for e in result]
        assert types == ["status", "tool_call", "status", "tool_result", "text", "done"]


# ==================== langgraph_stream (messages mode) ====================


class TestLanggraphStreamMessages:
    @pytest.mark.asyncio
    async def test_text_streaming(self):
        items = [
            (_MockAIMessageChunk(content="Hello"), {"langgraph_node": "agent"}),
            (_MockAIMessageChunk(content=" world"), {"langgraph_node": "agent"}),
        ]
        result = await _collect(langgraph_stream(_async_iter(items)))
        text_events = [e for e in result if e.type == "text"]
        assert len(text_events) == 2
        assert text_events[0].content == "Hello"
        assert text_events[1].content == " world"

    @pytest.mark.asyncio
    async def test_tool_calls(self):
        chunk = _MockAIMessageChunk(
            tool_calls=[{"id": "tc1", "name": "search", "args": {"q": "test"}}]
        )
        items = [(chunk, {"langgraph_node": "agent"})]
        result = await _collect(langgraph_stream(_async_iter(items)))
        tc_events = [e for e in result if e.type == "tool_call"]
        assert len(tc_events) == 1
        assert tc_events[0].tool_name == "search"
        assert tc_events[0].call_id == "tc1"

    @pytest.mark.asyncio
    async def test_tool_message(self):
        items = [
            (_MockToolMessage(content="result data", tool_call_id="tc1"), {"langgraph_node": "tools"}),
        ]
        result = await _collect(langgraph_stream(_async_iter(items)))
        tr_events = [e for e in result if e.type == "tool_result"]
        assert len(tr_events) == 1
        assert tr_events[0].result == "result data"
        assert tr_events[0].call_id == "tc1"

    @pytest.mark.asyncio
    async def test_node_status(self):
        items = [
            (_MockAIMessageChunk(content="hi"), {"langgraph_node": "agent"}),
            (_MockToolMessage(content="r", tool_call_id="tc1"), {"langgraph_node": "tools"}),
        ]
        result = await _collect(langgraph_stream(_async_iter(items)))
        status_events = [e for e in result if e.type == "status"]
        assert len(status_events) == 2
        assert "agent" in status_events[0].content
        assert "tools" in status_events[1].content

    @pytest.mark.asyncio
    async def test_no_status_when_disabled(self):
        items = [
            (_MockAIMessageChunk(content="hi"), {"langgraph_node": "agent"}),
        ]
        result = await _collect(langgraph_stream(_async_iter(items), include_status=False))
        status_events = [e for e in result if e.type == "status"]
        assert len(status_events) == 0

    @pytest.mark.asyncio
    async def test_done_emitted(self):
        items = [
            (_MockAIMessageChunk(content="hi"), {"langgraph_node": "agent"}),
        ]
        result = await _collect(langgraph_stream(_async_iter(items)))
        assert result[-1].type == "done"

    @pytest.mark.asyncio
    async def test_tool_call_dedup(self):
        chunk = _MockAIMessageChunk(
            tool_calls=[{"id": "tc1", "name": "search", "args": {}}]
        )
        items = [
            (chunk, {"langgraph_node": "agent"}),
            (chunk, {"langgraph_node": "agent"}),
        ]
        result = await _collect(langgraph_stream(_async_iter(items)))
        tc_events = [e for e in result if e.type == "tool_call"]
        assert len(tc_events) == 1

    @pytest.mark.asyncio
    async def test_dict_tool_message_content(self):
        items = [
            (_MockToolMessage(content={"key": "val"}, tool_call_id="tc1"), {"langgraph_node": "tools"}),
        ]
        result = await _collect(langgraph_stream(_async_iter(items)))
        tr = [e for e in result if e.type == "tool_result"][0]
        assert tr.result == '{"key": "val"}'


# ==================== langgraph_stream (updates mode) ====================


class TestLanggraphStreamUpdates:
    @pytest.mark.asyncio
    async def test_text_from_ai_message(self):
        updates = [
            {"agent": {"messages": [_MockAIMessage(content="Hello from agent")]}}
        ]
        result = await _collect(langgraph_stream(_async_iter(updates), stream_mode="updates"))
        text_events = [e for e in result if e.type == "text"]
        assert len(text_events) == 1
        assert text_events[0].content == "Hello from agent"

    @pytest.mark.asyncio
    async def test_tool_calls_from_ai_message(self):
        msg = _MockAIMessage(
            content="",
            tool_calls=[{"id": "tc1", "name": "search", "args": {"q": "test"}}],
        )
        updates = [{"agent": {"messages": [msg]}}]
        result = await _collect(langgraph_stream(_async_iter(updates), stream_mode="updates"))
        tc_events = [e for e in result if e.type == "tool_call"]
        assert len(tc_events) == 1
        assert tc_events[0].tool_name == "search"

    @pytest.mark.asyncio
    async def test_tool_result_from_tool_message(self):
        updates = [
            {"tools": {"messages": [_MockToolMessage(content="tool output", tool_call_id="tc1")]}}
        ]
        result = await _collect(langgraph_stream(_async_iter(updates), stream_mode="updates"))
        tr_events = [e for e in result if e.type == "tool_result"]
        assert len(tr_events) == 1
        assert tr_events[0].result == "tool output"

    @pytest.mark.asyncio
    async def test_node_status(self):
        updates = [
            {"agent": {"messages": [_MockAIMessage(content="hi")]}},
            {"tools": {"messages": [_MockToolMessage(content="r", tool_call_id="tc1")]}},
        ]
        result = await _collect(langgraph_stream(_async_iter(updates), stream_mode="updates"))
        status_events = [e for e in result if e.type == "status"]
        assert any("agent" in e.content for e in status_events)
        assert any("tools" in e.content for e in status_events)

    @pytest.mark.asyncio
    async def test_done_emitted(self):
        updates = [{"agent": {"messages": []}}]
        result = await _collect(langgraph_stream(_async_iter(updates), stream_mode="updates"))
        assert result[-1].type == "done"

    @pytest.mark.asyncio
    async def test_unsupported_mode_raises(self):
        with pytest.raises(ValueError, match="Unsupported stream_mode"):
            await _collect(langgraph_stream(_async_iter([]), stream_mode="invalid"))


# ==================== Import error ====================


# ==================== LangChainCallbackHandler ====================


class TestLangChainCallbackHandler:
    @pytest.mark.asyncio
    async def test_on_llm_new_token(self):
        handler = LangChainCallbackHandler()
        await handler.on_llm_new_token("Hello")
        await handler.on_llm_new_token(" world")
        handler.finish()

        events = await _collect(handler.events())
        text_events = [e for e in events if e.type == "text"]
        assert len(text_events) == 2
        assert text_events[0].content == "Hello"
        assert text_events[1].content == " world"

    @pytest.mark.asyncio
    async def test_empty_token_skipped(self):
        handler = LangChainCallbackHandler()
        await handler.on_llm_new_token("")
        handler.finish()

        events = await _collect(handler.events())
        text_events = [e for e in events if e.type == "text"]
        assert len(text_events) == 0

    @pytest.mark.asyncio
    async def test_tool_start_and_end(self):
        handler = LangChainCallbackHandler()
        await handler.on_tool_start(
            {"name": "search"}, '{"query": "test"}', run_id="tc1"
        )
        await handler.on_tool_end("Found 3 results", run_id="tc1")
        handler.finish()

        events = await _collect(handler.events())
        tc = [e for e in events if e.type == "tool_call"]
        tr = [e for e in events if e.type == "tool_result"]
        assert len(tc) == 1
        assert tc[0].tool_name == "search"
        assert tc[0].tool_input == {"query": "test"}
        assert tc[0].call_id == "tc1"
        assert len(tr) == 1
        assert tr[0].result == "Found 3 results"

    @pytest.mark.asyncio
    async def test_tool_start_plain_string_input(self):
        handler = LangChainCallbackHandler()
        await handler.on_tool_start({"name": "calc"}, "not json", run_id="tc2")
        handler.finish()

        events = await _collect(handler.events())
        tc = [e for e in events if e.type == "tool_call"][0]
        assert tc.tool_input == "not json"

    @pytest.mark.asyncio
    async def test_status_on_agent_chain_start(self):
        handler = LangChainCallbackHandler()
        await handler.on_chain_start({"name": "AgentExecutor"}, {})
        handler.finish()

        events = await _collect(handler.events())
        status = [e for e in events if e.type == "status"]
        assert len(status) == 1
        assert status[0].content == "Thinking..."

    @pytest.mark.asyncio
    async def test_no_status_when_disabled(self):
        handler = LangChainCallbackHandler(include_status=False)
        await handler.on_chain_start({"name": "AgentExecutor"}, {})
        await handler.on_tool_start({"name": "search"}, "{}", run_id="tc1")
        handler.finish()

        events = await _collect(handler.events())
        status = [e for e in events if e.type == "status"]
        assert len(status) == 0

    @pytest.mark.asyncio
    async def test_error_events(self):
        handler = LangChainCallbackHandler()
        await handler.on_tool_error(ValueError("bad input"))
        await handler.on_chain_error(RuntimeError("chain failed"))
        await handler.on_llm_error(ConnectionError("timeout"))
        handler.finish()

        events = await _collect(handler.events())
        errors = [e for e in events if e.type == "error"]
        assert len(errors) == 3
        assert "bad input" in errors[0].content
        assert "chain failed" in errors[1].content
        assert "timeout" in errors[2].content

    @pytest.mark.asyncio
    async def test_finish_with_metrics(self):
        handler = LangChainCallbackHandler()
        await handler.on_llm_new_token("Hi")
        handler.finish(metrics={"tokens": 100, "duration_ms": 500})

        events = await _collect(handler.events())
        done = [e for e in events if e.type == "done"]
        assert len(done) == 1
        assert done[0].metrics == {"tokens": 100, "duration_ms": 500}

    @pytest.mark.asyncio
    async def test_full_flow(self):
        handler = LangChainCallbackHandler()
        await handler.on_chain_start({"name": "Agent"}, {})
        await handler.on_tool_start({"name": "search"}, '{"q": "hi"}', run_id="tc1")
        await handler.on_tool_end("result", run_id="tc1")
        await handler.on_llm_new_token("Answer")
        handler.finish()

        events = await _collect(handler.events())
        types = [e.type for e in events]
        assert "status" in types
        assert "tool_call" in types
        assert "tool_result" in types
        assert "text" in types
        assert types[-1] == "done"


# ==================== to_langchain_tools ====================


class TestToLangchainTools:
    def test_from_registry(self):
        reg = ToolRegistry()

        @reg.tool
        def search(query: str) -> str:
            """Search the database."""
            return f"results for {query}"

        @reg.tool
        async def fetch(url: str) -> str:
            """Fetch a URL."""
            return url

        tools = to_langchain_tools(reg)
        assert len(tools) == 2
        assert tools[0].name == "search"
        assert tools[0].description == "Search the database."
        assert tools[0].func is not None  # sync → func
        assert tools[0].coroutine is None
        assert tools[1].name == "fetch"
        assert tools[1].coroutine is not None  # async → coroutine
        assert tools[1].func is None

    def test_from_tool_info_list(self):
        from kokage_ui.ai.tools import ToolInfo

        def my_fn(x: str) -> str:
            return x

        infos = [ToolInfo(name="test", description="A test", parameters={}, func=my_fn)]
        tools = to_langchain_tools(infos)
        assert len(tools) == 1
        assert tools[0].name == "test"

    def test_from_callable_list(self):
        def greet(name: str) -> str:
            """Say hello."""
            return f"Hello {name}"

        async def farewell(name: str) -> str:
            """Say goodbye."""
            return f"Bye {name}"

        tools = to_langchain_tools([greet, farewell])
        assert len(tools) == 2
        assert tools[0].name == "greet"
        assert tools[0].description == "Say hello."
        assert tools[1].name == "farewell"
        assert tools[1].coroutine is not None

    def test_invalid_source_raises(self):
        with pytest.raises(TypeError, match="Expected ToolRegistry"):
            to_langchain_tools("not a valid source")

    def test_non_callable_in_list_raises(self):
        with pytest.raises(TypeError, match="Expected callable"):
            to_langchain_tools([42])

    def test_handle_errors_passed(self):
        def fn(x: str) -> str:
            return x

        tools = to_langchain_tools([fn], handle_errors=False)
        assert tools[0].handle_tool_error is False

    def test_empty_registry(self):
        reg = ToolRegistry()
        tools = to_langchain_tools(reg)
        assert tools == []


# ==================== Import error ====================


class TestImportError:
    @pytest.mark.asyncio
    async def test_langchain_stream_import_message(self):
        """Verify helpful error message when langchain-core is missing."""
        # Save and remove mock
        saved = {
            k: sys.modules.pop(k)
            for k in list(sys.modules)
            if k.startswith("langchain_core")
        }
        try:
            import importlib
            from kokage_ui.ai import langchain as lc_mod

            importlib.reload(lc_mod)

            with pytest.raises(ImportError, match="langchain-core"):
                async for _ in lc_mod.langchain_stream(_async_iter([])):
                    pass
        finally:
            sys.modules.update(saved)
