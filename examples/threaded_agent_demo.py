"""Threaded agent demo — multiple persistent conversations.

Run:
    uv run uvicorn examples.threaded_agent_demo:app --reload
"""

import asyncio

from fastapi import FastAPI

from kokage_ui import AgentEvent, InMemoryConversationStore, KokageUI

app = FastAPI(title="Threaded Agent Demo")
ui = KokageUI(app)
store = InMemoryConversationStore()


@ui.threaded_agent("/", store=store, title="Threaded Agent Demo")
async def demo_agent(message: str, thread_id: str):
    """Simple echo agent with a simulated tool call."""
    yield AgentEvent(type="status", content="Thinking...")
    await asyncio.sleep(0.5)

    # Simulate a tool call
    yield AgentEvent(
        type="tool_call",
        call_id="tc1",
        tool_name="echo",
        tool_input={"message": message, "thread_id": thread_id},
    )
    await asyncio.sleep(0.3)
    yield AgentEvent(
        type="tool_result",
        call_id="tc1",
        result=f'{{"echo": "{message}", "thread": "{thread_id}"}}',
        preview_hint="json",
    )

    # Stream response text
    response = f"You said: **{message}**\n\nThis is thread `{thread_id}`."
    for char in response:
        yield AgentEvent(type="text", content=char)
        await asyncio.sleep(0.02)

    yield AgentEvent(
        type="done",
        metrics={"tokens": len(message) * 3, "duration_ms": 800, "tool_calls": 1},
    )
