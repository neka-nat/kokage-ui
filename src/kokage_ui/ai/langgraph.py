"""LangGraph integration adapter for kokage-ui AgentView.

Converts LangGraph ``astream`` output directly into SSE
``StreamingResponse`` for :class:`AgentView`.

Requires ``kokage-ui[langchain]`` (``langgraph >= 0.2``).

Example with ``stream_mode="messages"``::

    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    from kokage_ui.ai.langgraph import langgraph_agent_stream

    llm = ChatOpenAI(model="gpt-4o", streaming=True)
    agent = create_react_agent(llm, tools=[...])

    @app.post("/api/agent")
    async def run(request: Request):
        data = await request.json()
        stream = agent.astream(
            {"messages": [("user", data["message"])]},
            stream_mode="messages",
        )
        return langgraph_agent_stream(stream)

Example with ``stream_mode="updates"``::

    stream = agent.astream(
        {"messages": [("user", data["message"])]},
        stream_mode="updates",
    )
    return langgraph_agent_stream(stream, stream_mode="updates")
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from kokage_ui.ai.agent import AgentEvent, agent_stream
from starlette.responses import StreamingResponse


def langgraph_agent_stream(
    stream: AsyncIterator[Any],
    *,
    stream_mode: str = "messages",
    include_status: bool = True,
) -> StreamingResponse:
    """Convert LangGraph ``astream`` directly to SSE StreamingResponse.

    One-line adapter for use with :class:`AgentView`.

    Args:
        stream: Async iterator from ``graph.astream(...)``.
        stream_mode: Must match the ``stream_mode`` passed to ``astream()``.
            Supported: ``"messages"`` (default), ``"updates"``.
        include_status: Emit ``status`` events on node transitions.

    Returns:
        A ``StreamingResponse`` ready to return from a FastAPI endpoint.
    """
    return agent_stream(
        _langgraph_stream(stream, stream_mode=stream_mode, include_status=include_status)
    )


async def _langgraph_stream(
    stream: AsyncIterator[Any],
    *,
    stream_mode: str = "messages",
    include_status: bool = True,
) -> AsyncIterator[AgentEvent]:
    """Convert LangGraph ``astream`` output to :class:`AgentEvent` stream."""
    if stream_mode == "messages":
        async for item in _handle_messages_mode(stream, include_status=include_status):
            yield item
    elif stream_mode == "updates":
        async for item in _handle_updates_mode(stream, include_status=include_status):
            yield item
    else:
        raise ValueError(f"Unsupported stream_mode: {stream_mode!r}. Use 'messages' or 'updates'.")

    yield AgentEvent(type="done")


async def _handle_messages_mode(
    stream: AsyncIterator[Any],
    *,
    include_status: bool,
) -> AsyncIterator[AgentEvent]:
    """Handle ``stream_mode="messages"`` — yields ``(message_chunk, metadata)`` tuples."""
    try:
        from langchain_core.messages import AIMessageChunk, ToolMessage
    except ImportError:
        raise ImportError(
            "langchain-core is required for langgraph_stream. "
            "Install it with: pip install kokage-ui[langchain]"
        )

    tool_calls_seen: set[str] = set()
    current_node: str = ""

    async for chunk, metadata in stream:
        node = metadata.get("langgraph_node", "")
        if node != current_node:
            current_node = node
            if include_status and node:
                yield AgentEvent(type="status", content=f"Running {node}...")

        if isinstance(chunk, ToolMessage):
            content = chunk.content
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            yield AgentEvent(
                type="tool_result",
                call_id=chunk.tool_call_id or "",
                result=str(content),
            )
        elif isinstance(chunk, AIMessageChunk):
            # Text content
            if chunk.content:
                yield AgentEvent(type="text", content=chunk.content)

            # Tool calls
            for tc in getattr(chunk, "tool_calls", []) or []:
                tc_id = tc.get("id", "")
                if tc_id and tc_id not in tool_calls_seen:
                    tool_calls_seen.add(tc_id)
                    tool_input = tc.get("args", {})
                    yield AgentEvent(
                        type="tool_call",
                        call_id=tc_id,
                        tool_name=tc.get("name", ""),
                        tool_input=tool_input if isinstance(tool_input, (dict, str)) else str(tool_input),
                    )

            # tool_call_chunks (streaming partial)
            for tc in getattr(chunk, "tool_call_chunks", []) or []:
                tc_id = tc.get("id", "")
                if tc_id and tc_id not in tool_calls_seen:
                    tool_calls_seen.add(tc_id)
                    yield AgentEvent(
                        type="tool_call",
                        call_id=tc_id,
                        tool_name=tc.get("name", ""),
                        tool_input=tc.get("args", ""),
                    )


async def _handle_updates_mode(
    stream: AsyncIterator[Any],
    *,
    include_status: bool,
) -> AsyncIterator[AgentEvent]:
    """Handle ``stream_mode="updates"`` — yields ``{node_name: output_dict}``."""
    try:
        from langchain_core.messages import AIMessage, ToolMessage
    except ImportError:
        raise ImportError(
            "langchain-core is required for langgraph_stream. "
            "Install it with: pip install kokage-ui[langchain]"
        )

    async for update in stream:
        if not isinstance(update, dict):
            continue

        for node_name, node_output in update.items():
            if include_status:
                yield AgentEvent(type="status", content=f"Completed {node_name}")

            messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    content = msg.content
                    if isinstance(content, dict):
                        content = json.dumps(content, ensure_ascii=False)
                    yield AgentEvent(
                        type="tool_result",
                        call_id=msg.tool_call_id or "",
                        result=str(content),
                    )
                elif isinstance(msg, AIMessage):
                    if msg.content:
                        yield AgentEvent(type="text", content=str(msg.content))

                    for tc in getattr(msg, "tool_calls", []) or []:
                        tool_input = tc.get("args", {})
                        yield AgentEvent(
                            type="tool_call",
                            call_id=tc.get("id", ""),
                            tool_name=tc.get("name", ""),
                            tool_input=tool_input if isinstance(tool_input, (dict, str)) else str(tool_input),
                        )
