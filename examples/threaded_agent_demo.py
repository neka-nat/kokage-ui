"""Threaded agent demo — multiple persistent conversations with file attachments.

Run:
    uv run uvicorn examples.threaded_agent_demo:app --reload
"""

import asyncio
import os
import uuid

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from kokage_ui import AgentEvent, Attachment, InMemoryConversationStore, KokageUI

app = FastAPI(title="Threaded Agent Demo")
ui = KokageUI(app)
store = InMemoryConversationStore()

# Simple file storage to /tmp/uploads
UPLOAD_DIR = "/tmp/kokage_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


async def save_file(filename: str, upload_file) -> str:
    """Save uploaded file and return its URL."""
    ext = os.path.splitext(filename)[1]
    stored_name = f"{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    content = await upload_file.read()
    with open(path, "wb") as f:
        f.write(content)
    return f"/uploads/{stored_name}"


@ui.threaded_agent(
    "/",
    store=store,
    title="Threaded Agent Demo",
    file_handler=save_file,
    accept="image/*,.pdf,.txt,.csv,.json",
)
async def demo_agent(message: str, thread_id: str, attachments: list[Attachment]):
    """Echo agent with file attachment support."""
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

    # Build response
    parts = [f"You said: **{message}**"]
    if attachments:
        parts.append(f"\n\nReceived **{len(attachments)}** file(s):")
        for att in attachments:
            parts.append(f"\n- `{att.name}` ({att.content_type}, {att.size} bytes)")

    response = "".join(parts)
    for char in response:
        yield AgentEvent(type="text", content=char)
        await asyncio.sleep(0.01)

    yield AgentEvent(
        type="done",
        metrics={"tokens": len(message) * 3, "duration_ms": 800, "tool_calls": 1},
    )
