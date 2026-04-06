"""Deep Agents human-in-the-loop demo with interrupt approval.

Demonstrates how the interrupt_url parameter enables approval modals
for dangerous tool calls. Uses mock events to simulate Deep Agents
interrupt flow without requiring a real LLM.

Run:
    uv run uvicorn examples.deepagents_hitl_demo:app --reload

With a real Deep Agent (requires API key and checkpointer)::

    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver
    from kokage_ui.ai.deepagents import deep_agent_stream, deep_agent_resume

    agent = create_deep_agent(
        interrupt_on={"delete_file": True, "execute": True},
        checkpointer=MemorySaver(),
    )

    @app.post("/api/agent")
    async def run(request: Request):
        data = await request.json()
        return deep_agent_stream(agent, data["message"], thread_id="s1")

    @app.post("/api/agent/resume")
    async def resume(request: Request):
        data = await request.json()
        return deep_agent_resume(
            agent, decisions=data["decisions"], thread_id="s1",
        )
"""

import asyncio
import json

from fastapi import FastAPI, Request

from kokage_ui import KokageUI, Page
from kokage_ui.ai import AgentView, agent_stream
from kokage_ui.ai.agent import AgentEvent, AgentMessage

app = FastAPI()
ui = KokageUI(app)

# Track whether the mock agent is "interrupted"
_pending_interrupt: dict | None = None


@ui.page("/")
def agent_page():
    return Page(
        AgentView(
            send_url="/api/agent",
            interrupt_url="/api/agent/resume",
            messages=[
                AgentMessage(
                    role="assistant",
                    content=(
                        "Human-in-the-loop demo です。\n"
                        "危険なツール（delete_file, execute）の実行前に承認を求めます。\n"
                        "何か指示してください。"
                    ),
                ),
            ],
            agent_name="Deep Agent",
            user_name="You",
            height="700px",
        ),
        title="HITL Demo",
        include_marked=True,
        include_highlightjs=True,
    )


@app.post("/api/agent")
async def agent(request: Request):
    global _pending_interrupt
    data = await request.json()
    user_message = data["message"]

    async def run():
        # Step 1: Agent thinks
        yield AgentEvent(type="status", content="Thinking...")
        await asyncio.sleep(0.5)

        # Step 2: Agent decides to use a dangerous tool
        yield AgentEvent(type="text", content="了解しました。ファイルを削除します。\n\n")
        await asyncio.sleep(0.3)

        # Step 3: Tool call (shown in UI before interrupt)
        yield AgentEvent(
            type="tool_call",
            call_id="tc1",
            tool_name="delete_file",
            tool_input={"path": f"/tmp/{user_message.split()[0]}.txt"},
        )
        await asyncio.sleep(0.3)

        # Step 4: Interrupt — agent pauses for approval
        _pending_interrupt = {
            "tool_name": "delete_file",
            "tool_input": {"path": f"/tmp/{user_message.split()[0]}.txt"},
            "call_id": "tc1",
        }
        yield AgentEvent(
            type="interrupt",
            content="Approval required: delete_file",
            tool_name="delete_file",
            tool_input={"path": f"/tmp/{user_message.split()[0]}.txt"},
            metrics={
                "action_requests": [
                    {
                        "name": "delete_file",
                        "args": {"path": f"/tmp/{user_message.split()[0]}.txt"},
                    }
                ],
                "review_configs": [
                    {
                        "action_name": "delete_file",
                        "allowed_decisions": ["approve", "reject"],
                    }
                ],
                "thread_id": "demo-session",
            },
        )

    return agent_stream(run())


@app.post("/api/agent/resume")
async def resume(request: Request):
    global _pending_interrupt
    data = await request.json()
    decisions = data.get("decisions", [])

    async def run():
        info = _pending_interrupt
        _pending_interrupt = None

        if not decisions:
            yield AgentEvent(type="error", content="No decisions provided")
            yield AgentEvent(type="done")
            return

        decision_type = decisions[0].get("type", "reject")

        if decision_type == "approve":
            # Tool executes
            yield AgentEvent(type="status", content="Executing delete_file...")
            await asyncio.sleep(0.8)

            yield AgentEvent(
                type="tool_result",
                call_id=info["call_id"] if info else "tc1",
                result="File deleted successfully.",
            )
            await asyncio.sleep(0.3)

            # Agent continues
            response = "ファイルの削除が完了しました。他に何かありますか？"
            for char in response:
                yield AgentEvent(type="text", content=char)
                await asyncio.sleep(0.02)

            yield AgentEvent(
                type="done",
                metrics={"duration_ms": 2000, "tool_calls": 1},
            )

        else:
            # Rejected — agent responds accordingly
            yield AgentEvent(type="status", content="Tool execution rejected")
            await asyncio.sleep(0.3)

            response = "承知しました。ファイルの削除をキャンセルしました。別の方法で対応しましょうか？"
            for char in response:
                yield AgentEvent(type="text", content=char)
                await asyncio.sleep(0.02)

            yield AgentEvent(
                type="done",
                metrics={"duration_ms": 1000, "tool_calls": 0},
            )

    return agent_stream(run())
