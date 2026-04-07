"""Deep Agents plan visualization demo.

Demonstrates the DeepAgentView component with task plan sidebar
and file activity tracking. Uses mock events to simulate Deep Agents
write_todos and filesystem tool calls without requiring a real LLM.

Run:
    uv run uvicorn examples.deepagents_plan_demo:app --reload
"""

import asyncio
import json

from fastapi import FastAPI, Request

from kokage_ui import KokageUI, Page
from kokage_ui.ai import AgentMessage, agent_stream
from kokage_ui.ai.agent import AgentEvent
from kokage_ui.ai.deepagent_view import DeepAgentView

app = FastAPI()
ui = KokageUI(app)


@ui.page("/")
def plan_page():
    return Page(
        DeepAgentView(
            send_url="/api/agent",
            messages=[
                AgentMessage(
                    role="assistant",
                    content=(
                        "Deep Agent Plan Demo です。\n"
                        "タスクプランの進行とファイル操作をサイドバーで確認できます。\n"
                        "何か指示してください。"
                    ),
                ),
            ],
            agent_name="Deep Agent",
            user_name="You",
            height="700px",
            plan_label="Task Plan",
            files_label="File Activity",
        ),
        title="Plan Demo",
        include_marked=True,
        include_highlightjs=True,
    )


# Sample todo list that evolves over time
_TODOS_INITIAL = [
    {"task": "Analyze project structure", "status": "in_progress"},
    {"task": "Read configuration files", "status": "pending"},
    {"task": "Implement feature", "status": "pending"},
    {"task": "Write tests", "status": "pending"},
]

_TODOS_MID = [
    {"task": "Analyze project structure", "status": "completed"},
    {"task": "Read configuration files", "status": "in_progress"},
    {"task": "Implement feature", "status": "pending"},
    {"task": "Write tests", "status": "pending"},
]

_TODOS_FINAL = [
    {"task": "Analyze project structure", "status": "completed"},
    {"task": "Read configuration files", "status": "completed"},
    {"task": "Implement feature", "status": "in_progress"},
    {"task": "Write tests", "status": "pending"},
]


@app.post("/api/agent")
async def agent(request: Request):
    data = await request.json()

    async def run():
        # Step 1: Agent creates a plan
        yield AgentEvent(type="status", content="Planning...")
        await asyncio.sleep(0.5)

        yield AgentEvent(
            type="plan",
            content=json.dumps(_TODOS_INITIAL),
        )
        await asyncio.sleep(0.3)

        yield AgentEvent(type="text", content="まずプロジェクト構造を分析します。\n\n")
        await asyncio.sleep(0.5)

        # Step 2: Filesystem tool calls
        yield AgentEvent(
            type="tool_call",
            call_id="tc1",
            tool_name="ls",
            tool_input={"path": "/workspace/src"},
        )
        await asyncio.sleep(0.5)

        yield AgentEvent(
            type="tool_result",
            call_id="tc1",
            result="main.py\nutils.py\nconfig.yaml\ntests/",
        )
        await asyncio.sleep(0.3)

        # Step 3: Plan updates
        yield AgentEvent(
            type="plan",
            content=json.dumps(_TODOS_MID),
        )
        await asyncio.sleep(0.3)

        yield AgentEvent(type="text", content="設定ファイルを読み込みます。\n\n")
        await asyncio.sleep(0.3)

        yield AgentEvent(
            type="tool_call",
            call_id="tc2",
            tool_name="read_file",
            tool_input={"path": "/workspace/src/config.yaml"},
        )
        await asyncio.sleep(0.5)

        yield AgentEvent(
            type="tool_result",
            call_id="tc2",
            result="database:\n  host: localhost\n  port: 5432\n  name: myapp",
            preview_hint="yaml",
        )
        await asyncio.sleep(0.3)

        # Step 4: More progress
        yield AgentEvent(
            type="plan",
            content=json.dumps(_TODOS_FINAL),
        )
        await asyncio.sleep(0.3)

        yield AgentEvent(
            type="tool_call",
            call_id="tc3",
            tool_name="write_file",
            tool_input={"path": "/workspace/src/feature.py"},
        )
        await asyncio.sleep(0.5)

        yield AgentEvent(
            type="tool_result",
            call_id="tc3",
            result="File written successfully.",
        )
        await asyncio.sleep(0.3)

        # Final response
        response = "分析と実装を進めています。設定ファイルを読み込み、新しい機能ファイルを作成しました。"
        for char in response:
            yield AgentEvent(type="text", content=char)
            await asyncio.sleep(0.02)

        yield AgentEvent(
            type="done",
            metrics={"duration_ms": 5000, "tool_calls": 3},
        )

    return agent_stream(run())
