# Chat Demo

A streaming chat UI with a mock LLM that returns Markdown-formatted responses.

## Run

```bash
uvicorn examples.chat_demo:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Code

```python
--8<-- "examples/chat_demo.py"
```

## Features Demonstrated

- **ChatView** — Full chat interface with DaisyUI chat bubbles
- **ChatMessage** — Initial assistant greeting message
- **chat_stream** — SSE streaming response from async generator
- **Markdown rendering** — `include_marked=True` for rich text display
- **Code highlighting** — `include_highlightjs=True` for syntax highlighting in code blocks

## Key Patterns

### Streaming Response

```python
async def generate():
    for char in text:
        yield char
        await asyncio.sleep(0.02)  # Simulate LLM latency

return chat_stream(generate())
```

The `chat_stream()` helper wraps any async string generator into an SSE `StreamingResponse`. Each yielded string becomes a `{"token": "..."}` event.

### Custom Names

```python
ChatView(
    send_url="/api/chat",
    assistant_name="AI",
    user_name="あなた",
)
```

Display names appear in the chat bubble headers.
