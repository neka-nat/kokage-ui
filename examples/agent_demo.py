"""Agent demo with mock tool calls and streaming.

Run:
    uv run uvicorn examples.agent_demo:app --reload
"""

import asyncio

from fastapi import FastAPI, Request

from kokage_ui import KokageUI, Page
from kokage_ui.ai import AgentEvent, AgentMessage, AgentView, agent_stream

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
                    content="こんにちは！質問があればツールを使って調べます。",
                ),
            ],
            agent_name="Agent",
            user_name="あなた",
        ),
        title="Agent Demo",
    )


MOCK_RESULTS = {
    "default": "3件の結果が見つかりました:\n1. kokage-ui - FastAPIにUIを追加\n2. htmx - HTML拡張\n3. DaisyUI - Tailwindコンポーネント",
}

MOCK_RESPONSE = (
    "検索結果に基づいてお答えします。\n\n"
    "以下の関連情報が見つかりました：\n\n"
    "1. **kokage-ui** — FastAPIに簡単にUIを追加できるパッケージ\n"
    "2. **htmx** — HTMLをインタラクティブにする拡張\n"
    "3. **DaisyUI** — Tailwind CSSのコンポーネントライブラリ\n\n"
    "```python\n"
    "from kokage_ui import KokageUI, Page\n"
    "from kokage_ui.ai import AgentView\n"
    "```\n\n"
    "詳しく知りたいことがあればお聞きください！"
)


@app.post("/api/agent")
async def agent(request: Request):
    data = await request.json()
    user_message = data["message"]

    async def run():
        # Status update
        yield AgentEvent(type="status", content="考え中...")
        await asyncio.sleep(0.5)

        # Tool call
        yield AgentEvent(
            type="tool_call",
            call_id="tc1",
            tool_name="search",
            tool_input={"query": user_message, "limit": 3},
        )
        await asyncio.sleep(1.0)

        # Tool result
        yield AgentEvent(
            type="tool_result",
            call_id="tc1",
            result=MOCK_RESULTS["default"],
        )
        await asyncio.sleep(0.3)

        # Status update
        yield AgentEvent(type="status", content="回答を生成中...")
        await asyncio.sleep(0.3)

        # Stream text response
        for char in MOCK_RESPONSE:
            yield AgentEvent(type="text", content=char)
            await asyncio.sleep(0.02)

        # Done with metrics
        yield AgentEvent(
            type="done",
            metrics={"tokens": 250, "duration_ms": 3500, "tool_calls": 1},
        )

    return agent_stream(run())
