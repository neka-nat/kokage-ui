# Streaming Chat UI

kokage-ui provides a `ChatView` component for building LLM chat interfaces with SSE streaming, DaisyUI chat bubbles, Markdown rendering, and code highlighting.

## Quick Start

```python
from fastapi import FastAPI, Request
from kokage_ui import KokageUI, Page
from kokage_ui.ai import ChatView, ChatMessage, chat_stream

app = FastAPI()
ui = KokageUI(app)

@ui.page("/chat")
def chat_page():
    return Page(
        ChatView(send_url="/api/chat"),
        title="AI Chat",
        include_marked=True,
        include_highlightjs=True,
    )

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()

    async def generate():
        async for token in your_llm(data["message"]):
            yield token

    return chat_stream(generate())
```

## ChatView

The main chat UI component. Renders a message area with DaisyUI chat bubbles, an input form, and inline JavaScript for fetch-based SSE streaming.

```python
ChatView(
    send_url="/api/chat",
    messages=[
        ChatMessage(role="assistant", content="Hello! How can I help?"),
    ],
    assistant_name="AI",
    user_name="You",
    height="500px",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `send_url` | str | POST endpoint URL for sending messages (required) |
| `messages` | list[ChatMessage] \| None | Initial messages to display |
| `placeholder` | str | Input placeholder text (default: `"メッセージを入力..."`) |
| `send_label` | str | Submit button label (default: `"送信"`) |
| `stop_label` | str | Stop button label during streaming (default: `"停止"`) |
| `assistant_name` | str | Display name for assistant bubbles (default: `"Assistant"`) |
| `user_name` | str | Display name for user bubbles (default: `"You"`) |
| `height` | str | CSS height for the chat container (default: `"600px"`) |
| `chat_id` | str \| None | Unique ID prefix; auto-generated if omitted |

### Stop Button

During streaming, the send button transforms into a red stop button. Clicking it aborts the request via `AbortController`, preserving any content received so far.

```python
ChatView(send_url="/api/chat", stop_label="Cancel")
```

### Chat Bubble Layout

- **User messages** — aligned right with `chat-bubble-primary` styling
- **Assistant messages** — aligned left with `prose` class for Markdown content

## ChatMessage

A Pydantic BaseModel representing a single chat message.

```python
from kokage_ui.ai import ChatMessage

msg = ChatMessage(role="user", content="Hello!")
msg = ChatMessage(role="assistant", content="Hi there!", name="Bot")
```

| Field | Type | Description |
|-------|------|-------------|
| `role` | str | `"user"`, `"assistant"`, or `"system"` |
| `content` | str | Message text content |
| `name` | str \| None | Optional display name override |

## chat_stream

Helper function that converts an async token generator to an SSE `StreamingResponse`.

```python
from kokage_ui.ai import chat_stream

async def generate():
    yield "Hello"
    yield " world"

return chat_stream(generate())
```

Each token is sent as a Server-Sent Event:

```
data: {"token": "Hello"}

data: {"token": " world"}

data: {"done": true}
```

The response has `Content-Type: text/event-stream` with `Cache-Control: no-cache`.

## Markdown & Code Highlighting

`ChatView` automatically uses `marked.js` for Markdown rendering and `highlight.js` for code blocks when they are loaded on the page.

```python
Page(
    ChatView(send_url="/api/chat"),
    include_marked=True,        # Enable Markdown rendering
    include_highlightjs=True,   # Enable code syntax highlighting
)
```

If `marked.js` is not loaded, assistant messages are displayed as plain text with HTML escaping.

## Server-Side Endpoint

The POST endpoint receives JSON with a `message` field and should return a `chat_stream()` response:

```python
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data["message"]

    async def generate():
        # Use any LLM provider
        async for token in call_llm(user_message):
            yield token

    return chat_stream(generate())
```

### Request Format

```json
{"message": "user's input text"}
```

### Response Format

SSE stream where each event is a JSON object:

- `{"token": "..."}` — a text token to append
- `{"done": true}` — stream complete

## How It Works

1. User submits message via the input form
2. JavaScript adds a user chat bubble and an empty assistant bubble
3. `fetch()` sends a POST request to `send_url` with `{message: "..."}`
4. The response body is read as a stream using `ReadableStream`
5. Each SSE `data:` line is parsed; tokens are accumulated and rendered as Markdown
6. On `done`, code blocks are highlighted with `hljs` if available
7. The message area auto-scrolls to the latest message
8. During streaming, the send button shows a loading state
