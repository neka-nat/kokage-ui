"""LangChain integration adapter for kokage-ui AgentView.

Converts LangChain ``astream_events`` v2 output into :class:`AgentEvent` for
use with :func:`agent_stream`.  Also provides :class:`LangChainCallbackHandler`
for callback-based integration and :func:`to_langchain_tools` for converting
:class:`ToolRegistry` tools to LangChain ``BaseTool``.

Requires ``kokage-ui[langchain]`` (``langchain-core >= 0.3``).

Example::

    from langchain_openai import ChatOpenAI
    from kokage_ui.ai import agent_stream
    from kokage_ui.ai.langchain import langchain_stream

    llm = ChatOpenAI(model="gpt-4o", streaming=True)

    @app.post("/api/agent")
    async def agent(request: Request):
        data = await request.json()
        events = llm.astream_events(
            [{"role": "user", "content": data["message"]}], version="v2"
        )
        return agent_stream(langchain_stream(events))
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any

from kokage_ui.ai.agent import AgentEvent

_IMPORT_MSG = (
    "langchain-core is required for this feature. "
    "Install it with: pip install kokage-ui[langchain]"
)


async def langchain_stream(
    events: AsyncIterator[dict[str, Any]],
    *,
    include_status: bool = True,
) -> AsyncIterator[AgentEvent]:
    """Convert LangChain ``astream_events`` v2 to :class:`AgentEvent` stream.

    Args:
        events: Async iterator of LangChain event dicts from
            ``runnable.astream_events(..., version="v2")``.
        include_status: Emit ``status`` events on chain/tool start.
    """
    try:
        from langchain_core.messages import AIMessageChunk, ToolMessage  # noqa: F401
    except ImportError:
        raise ImportError(_IMPORT_MSG)

    tool_calls_seen: set[str] = set()

    async for event in events:
        kind = event.get("event", "")
        data = event.get("data", {})
        run_id = event.get("run_id", "")

        if kind == "on_chat_model_stream":
            chunk = data.get("chunk")
            if chunk is not None:
                # AIMessageChunk text content
                content = getattr(chunk, "content", "")
                if content:
                    yield AgentEvent(type="text", content=content)

                # Streaming tool calls (accumulated chunks)
                tc_chunks = getattr(chunk, "tool_call_chunks", [])
                for tc in tc_chunks:
                    tc_id = tc.get("id", "")
                    if tc_id and tc_id not in tool_calls_seen:
                        tool_calls_seen.add(tc_id)
                        tool_input = tc.get("args", "")
                        yield AgentEvent(
                            type="tool_call",
                            call_id=tc_id,
                            tool_name=tc.get("name", ""),
                            tool_input=tool_input if isinstance(tool_input, str) else tool_input,
                        )

        elif kind == "on_tool_start":
            tool_name = event.get("name", "")
            tool_input = data.get("input", "")
            if run_id not in tool_calls_seen:
                tool_calls_seen.add(run_id)
                yield AgentEvent(
                    type="tool_call",
                    call_id=run_id,
                    tool_name=tool_name,
                    tool_input=tool_input if isinstance(tool_input, (dict, str)) else str(tool_input),
                )
            if include_status:
                yield AgentEvent(type="status", content=f"Running {tool_name}...")

        elif kind == "on_tool_end":
            output = data.get("output", "")
            # ToolMessage has .content
            result = getattr(output, "content", None) if not isinstance(output, (str, dict)) else output
            if isinstance(result, dict):
                result = json.dumps(result, ensure_ascii=False)
            elif result is None:
                result = str(output)
            yield AgentEvent(
                type="tool_result",
                call_id=run_id,
                result=str(result),
            )

        elif kind == "on_chain_start" and include_status:
            name = event.get("name", "")
            if name and "agent" in name.lower():
                yield AgentEvent(type="status", content="Thinking...")

        elif kind == "on_chain_end":
            name = event.get("name", "")
            # Only emit done for the top-level agent chain
            if name and "agent" in name.lower():
                yield AgentEvent(type="done")


# ---------------------------------------------------------------------------
# LangChainCallbackHandler
# ---------------------------------------------------------------------------

_SENTINEL = object()


class LangChainCallbackHandler:
    """Async callback handler that converts LangChain callbacks to AgentEvent.

    Use with ``AgentExecutor`` or other runnables that accept callbacks
    but do not support ``astream_events``.

    Example::

        from kokage_ui.ai.langchain import LangChainCallbackHandler
        from kokage_ui.ai import agent_stream

        handler = LangChainCallbackHandler()

        async def run():
            task = asyncio.create_task(
                agent.ainvoke(
                    {"input": message},
                    config={"callbacks": [handler]},
                )
            )
            async for event in handler.events():
                yield event
            await task

        return agent_stream(run())
    """

    def __init__(self, *, include_status: bool = True) -> None:
        try:
            from langchain_core.callbacks import AsyncCallbackHandler  # noqa: F401
        except ImportError:
            raise ImportError(_IMPORT_MSG)
        self._queue: asyncio.Queue[AgentEvent | object] = asyncio.Queue()
        self._include_status = include_status

    def _put(self, event: AgentEvent) -> None:
        self._queue.put_nowait(event)

    async def events(self) -> AsyncIterator[AgentEvent]:
        """Async iterator that yields AgentEvents until done."""
        while True:
            item = await self._queue.get()
            if item is _SENTINEL:
                break
            yield item  # type: ignore[misc]

    def finish(self, metrics: dict | None = None) -> None:
        """Signal completion. Call after ``ainvoke`` finishes."""
        self._put(AgentEvent(type="done", metrics=metrics))
        self._queue.put_nowait(_SENTINEL)

    # -- LangChain AsyncCallbackHandler interface --

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        if token:
            self._put(AgentEvent(type="text", content=token))

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        call_id = str(run_id) if run_id else str(uuid.uuid4())
        tool_name = serialized.get("name", "") or kwargs.get("name", "")
        try:
            tool_input = json.loads(input_str)
        except (json.JSONDecodeError, TypeError):
            tool_input = input_str
        self._put(AgentEvent(
            type="tool_call",
            call_id=call_id,
            tool_name=tool_name,
            tool_input=tool_input,
        ))
        if self._include_status:
            self._put(AgentEvent(type="status", content=f"Running {tool_name}..."))

    async def on_tool_end(self, output: str, *, run_id: Any = None, **kwargs: Any) -> None:
        call_id = str(run_id) if run_id else ""
        self._put(AgentEvent(type="tool_result", call_id=call_id, result=str(output)))

    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        self._put(AgentEvent(type="error", content=str(error)))

    async def on_chain_start(
        self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs: Any
    ) -> None:
        if self._include_status:
            name = serialized.get("name", "")
            if name and "agent" in name.lower():
                self._put(AgentEvent(type="status", content="Thinking..."))

    async def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        pass  # done is signaled via finish()

    async def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        self._put(AgentEvent(type="error", content=str(error)))

    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        self._put(AgentEvent(type="error", content=str(error)))

    # Unused but required by interface
    async def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> None:
        pass

    async def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# to_langchain_tools
# ---------------------------------------------------------------------------


def to_langchain_tools(
    source: Any,
    *,
    handle_errors: bool = True,
) -> list:
    """Convert tools to LangChain ``BaseTool`` instances.

    Accepts a :class:`~kokage_ui.ai.tools.ToolRegistry`, a list of
    :class:`~kokage_ui.ai.tools.ToolInfo`, or a list of plain callables
    (sync or async functions with type hints and docstrings).

    Args:
        source: A ``ToolRegistry``, list of ``ToolInfo``, or list of callables.
        handle_errors: If True, tool errors are returned as strings instead of raising.

    Returns:
        List of LangChain ``StructuredTool`` instances.

    Example::

        from kokage_ui.ai.tools import ToolRegistry
        from kokage_ui.ai.langchain import to_langchain_tools

        registry = ToolRegistry()

        @registry.tool
        async def search(query: str) -> str:
            \"\"\"Search the database.\"\"\"
            return "results"

        lc_tools = to_langchain_tools(registry)
    """
    try:
        from langchain_core.tools import StructuredTool
    except ImportError:
        raise ImportError(_IMPORT_MSG)

    from kokage_ui.ai.tools import ToolInfo, ToolRegistry

    # Normalize input to list of ToolInfo
    if isinstance(source, ToolRegistry):
        tool_infos = source.list()
    elif isinstance(source, list) and source and isinstance(source[0], ToolInfo):
        tool_infos = source
    elif isinstance(source, list):
        # List of callables — wrap into ToolInfo
        from kokage_ui.ai.tools import _build_json_schema
        import inspect as _inspect

        tool_infos = []
        for fn in source:
            if not callable(fn):
                raise TypeError(f"Expected callable, got {type(fn)}")
            tool_infos.append(ToolInfo(
                name=fn.__name__,
                description=(_inspect.getdoc(fn) or "").strip() or fn.__name__,
                parameters=_build_json_schema(fn),
                func=fn,
            ))
    else:
        raise TypeError(
            f"Expected ToolRegistry, list of ToolInfo, or list of callables, got {type(source)}"
        )

    result = []
    for info in tool_infos:
        tool = StructuredTool.from_function(
            func=None if info.is_async else info.func,
            coroutine=info.func if info.is_async else None,
            name=info.name,
            description=info.description,
            handle_tool_error=handle_errors,
        )
        result.append(tool)

    return result
