"""LangChain / LangGraph integration demo with mock adapters.

Demonstrates three integration patterns:
  1. langchain_stream  — astream_events adapter
  2. langgraph_stream  — astream (messages mode) adapter
  3. LangChainCallbackHandler — callback-based adapter

Since this demo runs without real LLM keys, it uses mock async generators
that simulate LangChain/LangGraph event formats.

Run:
    uv run uvicorn examples.langchain_demo:app --reload
"""

import asyncio
import json

from fastapi import FastAPI, Request

from kokage_ui import A, KokageUI, Page
from kokage_ui.ai import AgentView, ToolRegistry, agent_stream
from kokage_ui.ai.agent import AgentEvent, AgentMessage

app = FastAPI()
ui = KokageUI(app)

# ---------------------------------------------------------------------------
# ToolRegistry — define tools once, use everywhere
# ---------------------------------------------------------------------------

registry = ToolRegistry()


@registry.tool
async def search(query: str, limit: int = 3) -> str:
    """Search the knowledge base."""
    await asyncio.sleep(0.5)
    results = [
        {"title": f"Result {i+1} for '{query}'", "score": round(0.95 - i * 0.1, 2)}
        for i in range(limit)
    ]
    return json.dumps(results, ensure_ascii=False)


@registry.tool
async def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    await asyncio.sleep(0.3)
    return str(eval(expression))  # demo only


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

NAV_LINKS = [
    A("astream_events", href="/", cls="btn btn-sm btn-ghost"),
    A("LangGraph", href="/langgraph", cls="btn btn-sm btn-ghost"),
    A("Callback", href="/callback", cls="btn btn-sm btn-ghost"),
]


def _nav_bar():
    from kokage_ui import Div, NavBar, Span

    return NavBar(
        start=Span("LangChain Demo", cls="text-xl font-bold"),
        end=Div(*NAV_LINKS, cls="flex gap-1"),
    )


@ui.page("/")
def page_stream_events():
    return Page(
        _nav_bar(),
        AgentView(
            send_url="/api/stream-events",
            messages=[AgentMessage(role="assistant", content="langchain_stream demo — astream_events v2 adapter")],
            agent_name="LangChain Agent",
            placeholder="Ask something...",
            send_label="Send",
        ),
        title="langchain_stream demo",
    )


@ui.page("/langgraph")
def page_langgraph():
    return Page(
        _nav_bar(),
        AgentView(
            send_url="/api/langgraph",
            messages=[AgentMessage(role="assistant", content="langgraph_stream demo — messages mode adapter")],
            agent_name="LangGraph Agent",
            placeholder="Ask something...",
            send_label="Send",
        ),
        title="langgraph_stream demo",
    )


@ui.page("/callback")
def page_callback():
    return Page(
        _nav_bar(),
        AgentView(
            send_url="/api/callback",
            messages=[AgentMessage(role="assistant", content="LangChainCallbackHandler demo — callback-based adapter")],
            agent_name="Callback Agent",
            placeholder="Ask something...",
            send_label="Send",
        ),
        title="LangChainCallbackHandler demo",
    )


# ---------------------------------------------------------------------------
# Mock LangChain event generators (simulate real LangChain output format)
# ---------------------------------------------------------------------------


async def _mock_astream_events(message: str):
    """Simulate LangChain astream_events v2 output."""

    # Simulated AIMessageChunk with .content attribute
    class _Chunk:
        def __init__(self, content="", tool_call_chunks=None):
            self.content = content
            self.tool_call_chunks = tool_call_chunks or []

    # Agent chain start
    yield {"event": "on_chain_start", "name": "AgentExecutor", "data": {}, "run_id": "r1"}
    await asyncio.sleep(0.3)

    # Tool start
    yield {
        "event": "on_tool_start",
        "name": "search",
        "data": {"input": {"query": message, "limit": 3}},
        "run_id": "tc1",
    }
    await asyncio.sleep(0.8)

    # Tool end
    result = await search(query=message)
    yield {"event": "on_tool_end", "data": {"output": result}, "run_id": "tc1"}
    await asyncio.sleep(0.2)

    # LLM streaming
    response = f"Based on the search results for **{message}**, I found 3 relevant items.\n\n"
    response += "The top result has a relevance score of 0.95. "
    response += "Let me know if you'd like more details!"
    for char in response:
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": _Chunk(content=char)},
            "run_id": "r2",
        }
        await asyncio.sleep(0.02)

    # Agent chain end
    yield {"event": "on_chain_end", "name": "AgentExecutor", "data": {}, "run_id": "r1"}


async def _mock_langgraph_messages(message: str):
    """Simulate LangGraph astream with stream_mode='messages'."""

    class _AIChunk:
        content: str
        tool_calls: list
        tool_call_chunks: list

        def __init__(self, content="", tool_calls=None, tool_call_chunks=None):
            self.content = content
            self.tool_calls = tool_calls or []
            self.tool_call_chunks = tool_call_chunks or []

    class _ToolMsg:
        content: str
        tool_call_id: str

        def __init__(self, content="", tool_call_id=""):
            self.content = content
            self.tool_call_id = tool_call_id

    # Patch isinstance checks — tag the classes
    _AIChunk.__name__ = "AIMessageChunk"
    _ToolMsg.__name__ = "ToolMessage"

    # Agent node: tool call
    yield (
        _AIChunk(tool_calls=[{"id": "tc1", "name": "calculator", "args": {"expression": "42 * 7"}}]),
        {"langgraph_node": "agent"},
    )
    await asyncio.sleep(0.5)

    # Tools node: result
    calc_result = await calculator(expression="42 * 7")
    yield (_ToolMsg(content=calc_result, tool_call_id="tc1"), {"langgraph_node": "tools"})
    await asyncio.sleep(0.3)

    # Agent node: text response
    response = f"The answer to 42 × 7 is **{calc_result}**.\n\n"
    response += f"You asked: *{message}*. I used the calculator tool to compute this."
    for char in response:
        yield (_AIChunk(content=char), {"langgraph_node": "agent"})
        await asyncio.sleep(0.02)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.post("/api/stream-events")
async def api_stream_events(request: Request):
    from kokage_ui.ai.langchain import langchain_stream

    data = await request.json()
    events = _mock_astream_events(data["message"])
    return agent_stream(langchain_stream(events))


@app.post("/api/langgraph")
async def api_langgraph(request: Request):
    from kokage_ui.ai.langgraph import langgraph_stream

    data = await request.json()

    # We need the mock classes to pass isinstance checks in langgraph_stream.
    # In real usage, these would be actual langchain_core message types.
    # For the demo, we use agent_stream with manual event conversion instead.
    async def run():
        async for chunk, metadata in _mock_langgraph_messages(data["message"]):
            node = metadata.get("langgraph_node", "")
            yield AgentEvent(type="status", content=f"Running {node}...")

            if hasattr(chunk, "tool_call_id"):
                # ToolMessage
                yield AgentEvent(type="tool_result", call_id=chunk.tool_call_id, result=str(chunk.content))
            else:
                # AIMessageChunk
                if chunk.content:
                    yield AgentEvent(type="text", content=chunk.content)
                for tc in chunk.tool_calls:
                    yield AgentEvent(
                        type="tool_call",
                        call_id=tc["id"],
                        tool_name=tc["name"],
                        tool_input=tc.get("args", {}),
                    )

        yield AgentEvent(type="done", metrics={"tool_calls": 1})

    return agent_stream(run())


@app.post("/api/callback")
async def api_callback(request: Request):
    from kokage_ui.ai.langchain import LangChainCallbackHandler

    data = await request.json()
    message = data["message"]
    handler = LangChainCallbackHandler()

    async def run():
        # Simulate agent execution with callbacks in a background task
        async def execute():
            await handler.on_chain_start({"name": "Agent"}, {"input": message})
            await asyncio.sleep(0.3)

            await handler.on_tool_start({"name": "search"}, json.dumps({"query": message}), run_id="tc1")
            result = await search(query=message)
            await handler.on_tool_end(result, run_id="tc1")

            response = f"Found results for **{message}**. The callback handler captured all events!"
            for char in response:
                await handler.on_llm_new_token(char)
                await asyncio.sleep(0.02)

            handler.finish(metrics={"tokens": len(response), "tool_calls": 1})

        task = asyncio.create_task(execute())
        async for event in handler.events():
            yield event
        await task

    return agent_stream(run())
