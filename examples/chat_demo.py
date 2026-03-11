"""Chat demo with mock LLM streaming.

Run:
    uv run uvicorn examples.chat_demo:app --reload
"""

import asyncio

from fastapi import FastAPI, Request

from kokage_ui import KokageUI, Page
from kokage_ui.ai import ChatMessage, ChatView, chat_stream

app = FastAPI()
ui = KokageUI(app)

MOCK_RESPONSE = (
    "こんにちは！何かお手伝いできることはありますか？\n\n"
    "例えば、以下のようなことができます：\n\n"
    "- **質問に回答** する\n"
    "- **コードを書く** ことをサポートする\n"
    "- **文章を要約** する\n\n"
    "```python\n"
    'print("Hello, World!")\n'
    "```\n\n"
    "お気軽にどうぞ！"
)


@ui.page("/")
def chat_page():
    return Page(
        ChatView(
            send_url="/api/chat",
            messages=[
                ChatMessage(role="assistant", content="こんにちは！何でも聞いてください。"),
            ],
            assistant_name="AI",
            user_name="あなた",
        ),
        title="Chat Demo",
    )


@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data["message"]

    async def generate():
        # Mock LLM: stream the response character by character
        for char in MOCK_RESPONSE:
            yield char
            await asyncio.sleep(0.02)

    return chat_stream(generate())
