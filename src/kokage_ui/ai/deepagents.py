"""Deep Agents integration adapter for kokage-ui AgentView.

Converts a ``create_deep_agent()`` compiled graph into SSE
``StreamingResponse`` for :class:`AgentView`, with special handling
for Deep Agents built-in tools (write_todos, filesystem, task).

Requires ``kokage-ui[deepagents]`` (``deepagents >= 0.1``).

Basic usage::

    from deepagents import create_deep_agent
    from kokage_ui.ai.deepagents import deep_agent_stream

    agent = create_deep_agent(
        tools=[my_tool],
        system_prompt="You are a helpful assistant",
    )

    @app.post("/api/agent")
    async def run(request: Request):
        data = await request.json()
        return deep_agent_stream(agent, data["message"])

With conversation persistence (checkpointer)::

    from langgraph.checkpoint.memory import MemorySaver

    agent = create_deep_agent(
        tools=[my_tool],
        checkpointer=MemorySaver(),
    )

    @app.post("/api/agent")
    async def run(request: Request):
        data = await request.json()
        return deep_agent_stream(
            agent,
            data["message"],
            thread_id=data.get("thread_id", "default"),
        )

With human-in-the-loop (interrupt_on)::

    agent = create_deep_agent(
        tools=[delete_file, send_email],
        interrupt_on={"delete_file": True, "send_email": True},
        checkpointer=MemorySaver(),
    )

    @app.post("/api/agent")
    async def run(request: Request):
        data = await request.json()
        return deep_agent_stream(
            agent, data["message"], thread_id="session-1",
        )

    @app.post("/api/agent/resume")
    async def resume(request: Request):
        data = await request.json()
        return deep_agent_resume(
            agent,
            decisions=data["decisions"],
            thread_id="session-1",
        )

With kokage-ui ToolRegistry::

    from kokage_ui.ai import ToolRegistry
    from kokage_ui.ai.deepagents import to_deep_agent_tools

    registry = ToolRegistry()

    @registry.tool
    async def search(query: str) -> str:
        \"\"\"Search the database.\"\"\"
        return "results"

    agent = create_deep_agent(tools=to_deep_agent_tools(registry))
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from kokage_ui.ai.agent import AgentEvent, agent_stream
from starlette.responses import StreamingResponse


# File extensions → preview hints for filesystem tool results.
_EXT_HINTS: dict[str, str] = {
    ".json": "json",
    ".csv": "csv",
    ".tsv": "csv",
    ".md": "markdown",
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".sh": "bash",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".svg": "image",
}

# Deep Agents built-in filesystem tools.
_FILESYSTEM_TOOLS = {"read_file", "write_file", "edit_file", "ls", "glob", "grep"}


def _guess_preview_hint(tool_name: str, tool_input: Any) -> str:
    """Guess a preview hint from filesystem tool name and input path."""
    if tool_name not in _FILESYSTEM_TOOLS:
        return ""
    # Extract path from tool input
    path = ""
    if isinstance(tool_input, dict):
        path = tool_input.get("path", tool_input.get("file_path", ""))
    elif isinstance(tool_input, str):
        path = tool_input
    if not path:
        return ""
    _, ext = os.path.splitext(path)
    return _EXT_HINTS.get(ext.lower(), "")


def _detect_result_hint(result: str, tool_name: str) -> str:
    """Detect preview hint from tool result content."""
    if not result:
        return ""
    stripped = result.strip()
    # JSON detection
    if stripped.startswith(("{", "[")):
        try:
            json.loads(stripped)
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass
    # ls/glob results look like file listings
    if tool_name in ("ls", "glob"):
        return ""
    return ""


class DeepAgentConfig(BaseModel):
    """Configuration for deep_agent_stream behavior.

    Args:
        include_status: Emit status events on node transitions.
        include_plan: Emit plan events when write_todos is called.
        include_metrics: Collect and emit execution metrics in done event.
        stream_mode: LangGraph stream mode — ``"messages"`` or ``"updates"``.
    """

    include_status: bool = True
    include_plan: bool = True
    include_metrics: bool = True
    stream_mode: str = "messages"


def deep_agent_stream(
    agent: Any,
    message: str,
    *,
    thread_id: str | None = None,
    config: DeepAgentConfig | None = None,
    extra_config: dict[str, Any] | None = None,
) -> StreamingResponse:
    """Stream a Deep Agent response as SSE for AgentView.

    One-line adapter: pass the compiled graph from ``create_deep_agent()``
    and a user message, get back a ``StreamingResponse``.

    Args:
        agent: Compiled graph from ``create_deep_agent()``.
        message: User message string.
        thread_id: Optional thread ID for conversation persistence
            (requires a checkpointer on the agent).
        config: Adapter configuration. Uses defaults if omitted.
        extra_config: Additional LangGraph config dict merged into
            the invocation config (e.g. ``{"recursion_limit": 50}``).

    Returns:
        A ``StreamingResponse`` with ``text/event-stream`` content type.
    """
    cfg = config or DeepAgentConfig()
    return agent_stream(
        _deep_agent_events(
            agent,
            message,
            thread_id=thread_id,
            config=cfg,
            extra_config=extra_config,
        )
    )


def _build_invoke_config(
    thread_id: str | None = None,
    extra_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build LangGraph invocation config dict."""
    invoke_config: dict[str, Any] = {}
    if thread_id is not None:
        invoke_config["configurable"] = {"thread_id": thread_id}
    if extra_config:
        invoke_config.update(extra_config)
    return invoke_config


def _check_interrupt(agent: Any, invoke_config: dict[str, Any]) -> dict[str, Any] | None:
    """Check if the agent is paused at an interrupt.

    Returns interrupt info dict if interrupted, None otherwise.
    The returned dict has keys: ``action_requests``, ``review_configs``.
    """
    get_state = getattr(agent, "get_state", None)
    if get_state is None:
        return None

    try:
        state = get_state(invoke_config if invoke_config else None)
    except Exception:
        return None

    # LangGraph v2: state has .tasks with interrupts
    tasks = getattr(state, "tasks", None)
    if tasks:
        for task in tasks:
            interrupts = getattr(task, "interrupts", None)
            if interrupts:
                # Deep Agents HITL interrupt value contains action_requests
                for intr in interrupts:
                    value = getattr(intr, "value", None)
                    if isinstance(value, dict) and "action_requests" in value:
                        return value

    # Fallback: check state.next (pending nodes indicate interrupt)
    next_nodes = getattr(state, "next", None)
    if next_nodes:
        # Generic interrupt — we know execution paused but no structured info
        return {"action_requests": [], "review_configs": []}

    return None


def _interrupt_to_event(interrupt_info: dict[str, Any], thread_id: str | None) -> AgentEvent:
    """Convert interrupt info dict to an AgentEvent."""
    action_requests = interrupt_info.get("action_requests", [])
    review_configs = interrupt_info.get("review_configs", [])

    # Build human-readable summary
    tool_names_list = [ar.get("name", "unknown") for ar in action_requests]
    summary = ", ".join(tool_names_list) if tool_names_list else "tool execution"

    # Primary tool info for the event fields
    first_tool_name = ""
    first_tool_input: dict | str = ""
    if action_requests:
        first = action_requests[0]
        first_tool_name = first.get("name", "")
        first_tool_input = first.get("args", {})

    return AgentEvent(
        type="interrupt",
        content=f"Approval required: {summary}",
        tool_name=first_tool_name,
        tool_input=first_tool_input,
        metrics={
            "action_requests": action_requests,
            "review_configs": review_configs,
            "thread_id": thread_id,
        },
    )


async def _deep_agent_events(
    agent: Any,
    message: str,
    *,
    thread_id: str | None = None,
    config: DeepAgentConfig,
    extra_config: dict[str, Any] | None = None,
) -> AsyncIterator[AgentEvent]:
    """Convert Deep Agent streaming output to AgentEvent stream."""
    try:
        from langchain_core.messages import AIMessageChunk, ToolMessage
    except ImportError:
        raise ImportError(
            "langchain-core is required for deep_agent_stream. "
            "Install it with: pip install kokage-ui[deepagents]"
        )

    invoke_config = _build_invoke_config(thread_id, extra_config)
    input_data = {"messages": [("user", message)]}

    tool_calls_seen: set[str] = set()
    current_node: str = ""
    tool_inputs: dict[str, Any] = {}
    tool_names: dict[str, str] = {}
    start_time = time.monotonic()
    token_count = 0
    tool_call_count = 0

    try:
        stream = agent.astream(
            input_data,
            config=invoke_config if invoke_config else None,
            stream_mode=config.stream_mode,
        )

        if config.stream_mode == "messages":
            async for item in _handle_messages(
                stream,
                config=config,
                tool_calls_seen=tool_calls_seen,
                tool_inputs=tool_inputs,
                tool_names=tool_names,
                state={"current_node": current_node, "token_count": 0, "tool_call_count": 0},
            ):
                yield item
                if item.type == "text":
                    token_count += len(item.content)
                elif item.type == "tool_call":
                    tool_call_count += 1

        elif config.stream_mode == "updates":
            async for item in _handle_updates(
                stream,
                config=config,
                tool_inputs=tool_inputs,
                tool_names=tool_names,
            ):
                yield item
                if item.type == "text":
                    token_count += len(item.content)
                elif item.type == "tool_call":
                    tool_call_count += 1
        else:
            raise ValueError(
                f"Unsupported stream_mode: {config.stream_mode!r}. "
                "Use 'messages' or 'updates'."
            )

    except Exception as e:
        yield AgentEvent(type="error", content=str(e))

    # Check for pending interrupts (HITL)
    interrupt_info = _check_interrupt(agent, invoke_config)
    if interrupt_info is not None:
        yield _interrupt_to_event(interrupt_info, thread_id)
        return  # Do NOT emit "done" — client should resume or reject

    # Done event with metrics
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    metrics: dict[str, Any] | None = None
    if config.include_metrics:
        metrics = {
            "duration_ms": elapsed_ms,
            "tool_calls": tool_call_count,
        }
    yield AgentEvent(type="done", metrics=metrics)


def deep_agent_resume(
    agent: Any,
    *,
    decisions: list[dict[str, Any]],
    thread_id: str,
    config: DeepAgentConfig | None = None,
    extra_config: dict[str, Any] | None = None,
) -> StreamingResponse:
    """Resume a Deep Agent after an interrupt with approval decisions.

    Call this from your resume endpoint after the user approves, rejects,
    or edits tool calls shown in the interrupt modal.

    Args:
        agent: The same compiled graph used in ``deep_agent_stream()``.
        decisions: List of decision dicts, one per pending tool call.
            Each dict has ``"type"`` (``"approve"``, ``"reject"``, or
            ``"edit"``) and optionally ``"edited_action"`` for edits.
        thread_id: The thread ID from the interrupt event's metrics.
        config: Adapter configuration. Uses defaults if omitted.
        extra_config: Additional LangGraph config dict.

    Returns:
        A ``StreamingResponse`` continuing the agent execution.

    Example decisions::

        # Approve all
        [{"type": "approve"}]

        # Reject
        [{"type": "reject"}]

        # Edit arguments
        [{"type": "edit", "edited_action": {"name": "send_email", "args": {"to": "new@example.com"}}}]
    """
    cfg = config or DeepAgentConfig()
    return agent_stream(
        _deep_agent_resume_events(
            agent,
            decisions=decisions,
            thread_id=thread_id,
            config=cfg,
            extra_config=extra_config,
        )
    )


async def _deep_agent_resume_events(
    agent: Any,
    *,
    decisions: list[dict[str, Any]],
    thread_id: str,
    config: DeepAgentConfig,
    extra_config: dict[str, Any] | None = None,
) -> AsyncIterator[AgentEvent]:
    """Resume agent execution after interrupt and stream events."""
    try:
        from langchain_core.messages import AIMessageChunk, ToolMessage
        from langgraph.types import Command
    except ImportError:
        raise ImportError(
            "langchain-core and langgraph are required for deep_agent_resume. "
            "Install with: pip install kokage-ui[deepagents]"
        )

    invoke_config = _build_invoke_config(thread_id, extra_config)

    tool_calls_seen: set[str] = set()
    tool_inputs: dict[str, Any] = {}
    tool_names: dict[str, str] = {}
    start_time = time.monotonic()
    token_count = 0
    tool_call_count = 0

    try:
        resume_value = Command(resume={"decisions": decisions})

        stream = agent.astream(
            resume_value,
            config=invoke_config if invoke_config else None,
            stream_mode=config.stream_mode,
        )

        if config.stream_mode == "messages":
            async for item in _handle_messages(
                stream,
                config=config,
                tool_calls_seen=tool_calls_seen,
                tool_inputs=tool_inputs,
                tool_names=tool_names,
                state={},
            ):
                yield item
                if item.type == "text":
                    token_count += len(item.content)
                elif item.type == "tool_call":
                    tool_call_count += 1

        elif config.stream_mode == "updates":
            async for item in _handle_updates(
                stream,
                config=config,
                tool_inputs=tool_inputs,
                tool_names=tool_names,
            ):
                yield item
                if item.type == "text":
                    token_count += len(item.content)
                elif item.type == "tool_call":
                    tool_call_count += 1

    except Exception as e:
        yield AgentEvent(type="error", content=str(e))

    # Check for another interrupt (chained approvals)
    interrupt_info = _check_interrupt(agent, invoke_config)
    if interrupt_info is not None:
        yield _interrupt_to_event(interrupt_info, thread_id)
        return

    # Done event
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    metrics: dict[str, Any] | None = None
    if config.include_metrics:
        metrics = {
            "duration_ms": elapsed_ms,
            "tool_calls": tool_call_count,
        }
    yield AgentEvent(type="done", metrics=metrics)


async def _handle_messages(
    stream: AsyncIterator[Any],
    *,
    config: DeepAgentConfig,
    tool_calls_seen: set[str],
    tool_inputs: dict[str, Any],
    tool_names: dict[str, str],
    state: dict[str, Any],
) -> AsyncIterator[AgentEvent]:
    """Handle ``stream_mode="messages"`` for Deep Agents."""
    try:
        from langchain_core.messages import AIMessageChunk, ToolMessage
    except ImportError:
        return

    current_node = state.get("current_node", "")

    async for chunk, metadata in stream:
        node = metadata.get("langgraph_node", "")
        if node != current_node:
            current_node = node
            if config.include_status and node:
                yield AgentEvent(type="status", content=f"Running {node}...")

        if isinstance(chunk, ToolMessage):
            call_id = chunk.tool_call_id or ""
            content = chunk.content
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            result_str = str(content)

            # Determine preview hint
            t_name = tool_names.get(call_id, "")
            hint = _guess_preview_hint(t_name, tool_inputs.get(call_id))
            if not hint:
                hint = _detect_result_hint(result_str, t_name)

            # Emit plan event for write_todos
            if config.include_plan and t_name == "write_todos":
                yield AgentEvent(
                    type="plan",
                    content=result_str,
                )

            yield AgentEvent(
                type="tool_result",
                call_id=call_id,
                result=result_str,
                preview_hint=hint,
            )

        elif isinstance(chunk, AIMessageChunk):
            # Text content
            if chunk.content:
                yield AgentEvent(type="text", content=chunk.content)

            # Full tool calls
            for tc in getattr(chunk, "tool_calls", []) or []:
                tc_id = tc.get("id", "")
                if tc_id and tc_id not in tool_calls_seen:
                    tool_calls_seen.add(tc_id)
                    t_name = tc.get("name", "")
                    t_input = tc.get("args", {})
                    tool_inputs[tc_id] = t_input
                    tool_names[tc_id] = t_name
                    yield AgentEvent(
                        type="tool_call",
                        call_id=tc_id,
                        tool_name=t_name,
                        tool_input=t_input if isinstance(t_input, (dict, str)) else str(t_input),
                    )

            # Streaming partial tool call chunks
            for tc in getattr(chunk, "tool_call_chunks", []) or []:
                tc_id = tc.get("id", "")
                if tc_id and tc_id not in tool_calls_seen:
                    tool_calls_seen.add(tc_id)
                    t_name = tc.get("name", "")
                    t_input = tc.get("args", "")
                    tool_inputs[tc_id] = t_input
                    tool_names[tc_id] = t_name
                    yield AgentEvent(
                        type="tool_call",
                        call_id=tc_id,
                        tool_name=t_name,
                        tool_input=t_input,
                    )


async def _handle_updates(
    stream: AsyncIterator[Any],
    *,
    config: DeepAgentConfig,
    tool_inputs: dict[str, Any],
    tool_names: dict[str, str],
) -> AsyncIterator[AgentEvent]:
    """Handle ``stream_mode="updates"`` for Deep Agents."""
    try:
        from langchain_core.messages import AIMessage, ToolMessage
    except ImportError:
        return

    async for update in stream:
        if not isinstance(update, dict):
            continue

        for node_name, node_output in update.items():
            if config.include_status:
                yield AgentEvent(type="status", content=f"Completed {node_name}")

            messages = node_output.get("messages", []) if isinstance(node_output, dict) else []
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    call_id = msg.tool_call_id or ""
                    content = msg.content
                    if isinstance(content, dict):
                        content = json.dumps(content, ensure_ascii=False)
                    result_str = str(content)

                    t_name = tool_names.get(call_id, "")
                    hint = _guess_preview_hint(t_name, tool_inputs.get(call_id))
                    if not hint:
                        hint = _detect_result_hint(result_str, t_name)

                    if config.include_plan and t_name == "write_todos":
                        yield AgentEvent(type="plan", content=result_str)

                    yield AgentEvent(
                        type="tool_result",
                        call_id=call_id,
                        result=result_str,
                        preview_hint=hint,
                    )

                elif isinstance(msg, AIMessage):
                    if msg.content:
                        yield AgentEvent(type="text", content=str(msg.content))

                    for tc in getattr(msg, "tool_calls", []) or []:
                        tc_id = tc.get("id", "")
                        t_name = tc.get("name", "")
                        t_input = tc.get("args", {})
                        tool_inputs[tc_id] = t_input
                        tool_names[tc_id] = t_name
                        yield AgentEvent(
                            type="tool_call",
                            call_id=tc_id,
                            tool_name=t_name,
                            tool_input=t_input if isinstance(t_input, (dict, str)) else str(t_input),
                        )


def to_deep_agent_tools(source: Any) -> list:
    """Convert kokage-ui ToolRegistry to a list of callables for Deep Agents.

    Deep Agents accepts plain Python functions (with docstrings and type hints)
    as tools via ``create_deep_agent(tools=[...])``.

    Args:
        source: A :class:`~kokage_ui.ai.tools.ToolRegistry` or a list
            of :class:`~kokage_ui.ai.tools.ToolInfo` objects.

    Returns:
        A list of callables suitable for ``create_deep_agent(tools=...)``.
    """
    from kokage_ui.ai.tools import ToolInfo, ToolRegistry

    if isinstance(source, ToolRegistry):
        infos = source.list()
    elif isinstance(source, list) and all(isinstance(t, ToolInfo) for t in source):
        infos = source
    else:
        raise TypeError(
            f"Expected ToolRegistry or list[ToolInfo], got {type(source).__name__}"
        )

    return [info.func for info in infos if info.func is not None]
