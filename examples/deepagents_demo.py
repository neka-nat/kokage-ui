"""Deep Agents integration demo with mock streaming.

Demonstrates how to connect a Deep Agent to kokage-ui's AgentView
using ``deep_agent_stream()``.

Since this demo runs without real LLM keys, it uses a mock agent
that simulates Deep Agents streaming (write_todos, filesystem tools,
subagent task delegation, and text generation).

Run:
    uv run uvicorn examples.deepagents_demo:app --reload

With a real Deep Agent (requires API key)::

    from deepagents import create_deep_agent
    from kokage_ui.ai.deepagents import deep_agent_stream

    agent = create_deep_agent(system_prompt="You are a helpful assistant")

    @app.post("/api/agent")
    async def run(request: Request):
        data = await request.json()
        return deep_agent_stream(agent, data["message"])
"""

import asyncio
import json

from fastapi import FastAPI, Request

from kokage_ui import KokageUI, Page
from kokage_ui.ai import AgentView, agent_stream
from kokage_ui.ai.agent import AgentEvent, AgentMessage

app = FastAPI()
ui = KokageUI(app)


@ui.page("/")
def agent_page():
    return Page(
        AgentView(
            send_url="/api/agent",
            messages=[
                AgentMessage(
                    role="assistant",
                    content="Deep Agents demo です。質問があればツールを使って調べます。",
                ),
            ],
            agent_name="Deep Agent",
            user_name="You",
            height="700px",
        ),
        title="Deep Agents Demo",
        include_marked=True,
        include_highlightjs=True,
    )


# ---------------------------------------------------------------------------
# Mock Deep Agent streaming (simulates write_todos + read_file + text)
# ---------------------------------------------------------------------------

MOCK_TODOS = json.dumps(
    [
        {"task": "Search for relevant information", "status": "completed"},
        {"task": "Read configuration file", "status": "in_progress"},
        {"task": "Generate summary response", "status": "pending"},
    ],
    ensure_ascii=False,
    indent=2,
)

MOCK_FILE_CONTENT = """\
[project]
name = "kokage-ui"
version = "0.7.0"
description = "Add htmx + DaisyUI based UI to FastAPI with pure Python"
requires-python = ">=3.11"
"""

MOCK_RESPONSE = (
    "調査が完了しました。\n\n"
    "## 結果\n\n"
    "1. **kokage-ui** はFastAPIにhtmx + DaisyUIベースのUIを追加するパッケージです\n"
    "2. Python 3.11以上が必要です\n"
    "3. 現在のバージョンは **0.7.0** です\n\n"
    "```python\n"
    "from kokage_ui import KokageUI, Page\n"
    "from kokage_ui.ai import AgentView\n"
    "```\n\n"
    "他に質問があればお聞きください！"
)


@app.post("/api/agent")
async def agent(request: Request):
    data = await request.json()
    user_message = data["message"]

    async def run():
        # Step 1: Planning (write_todos)
        yield AgentEvent(type="status", content="Planning...")
        await asyncio.sleep(0.3)

        yield AgentEvent(
            type="tool_call",
            call_id="tc1",
            tool_name="write_todos",
            tool_input={"todos": user_message},
        )
        await asyncio.sleep(0.5)
        yield AgentEvent(
            type="tool_result",
            call_id="tc1",
            result=MOCK_TODOS,
            preview_hint="json",
        )
        yield AgentEvent(type="status", content="Plan updated")
        await asyncio.sleep(0.3)

        # Step 2: Filesystem tool (read_file)
        yield AgentEvent(
            type="tool_call",
            call_id="tc2",
            tool_name="read_file",
            tool_input={"path": "pyproject.toml"},
        )
        await asyncio.sleep(0.8)
        yield AgentEvent(
            type="tool_result",
            call_id="tc2",
            result=MOCK_FILE_CONTENT,
            preview_hint="toml",
        )
        await asyncio.sleep(0.2)

        # Step 3: Stream text response
        yield AgentEvent(type="status", content="Generating response...")
        await asyncio.sleep(0.2)

        for char in MOCK_RESPONSE:
            yield AgentEvent(type="text", content=char)
            await asyncio.sleep(0.015)

        # Done
        yield AgentEvent(
            type="done",
            metrics={"duration_ms": 3200, "tool_calls": 2},
        )

    return agent_stream(run())
