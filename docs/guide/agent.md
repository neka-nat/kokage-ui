# Agent View

kokage-ui provides an `AgentView` component for building AI agent dashboards with SSE streaming, tool call visualization, status bar, and metrics display.

## Quick Start

```python
from fastapi import FastAPI, Request
from kokage_ui import KokageUI, Page
from kokage_ui.ai import AgentView, AgentEvent, AgentMessage, agent_stream

app = FastAPI()
ui = KokageUI(app)

@ui.page("/")
def agent_page():
    return Page(
        AgentView(send_url="/api/agent", agent_name="Agent"),
        title="Agent",
        include_marked=True,
        include_highlightjs=True,
    )

@app.post("/api/agent")
async def agent(request: Request):
    data = await request.json()

    async def run():
        yield AgentEvent(type="status", content="Thinking...")
        yield AgentEvent(type="tool_call", call_id="tc1", tool_name="search",
                         tool_input={"q": data["message"]})
        result = await do_search(data["message"])
        yield AgentEvent(type="tool_result", call_id="tc1", result=result)
        async for token in call_llm(data["message"], result):
            yield AgentEvent(type="text", content=token)
        yield AgentEvent(type="done", metrics={"tokens": 150, "duration_ms": 2500, "tool_calls": 1})

    return agent_stream(run())
```

## AgentView

The main agent dashboard component. Renders a status bar, message area with tool call panels, metrics bar, input form, and inline JavaScript for SSE streaming.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `send_url` | str | (required) | POST endpoint URL |
| `interrupt_url` | str \| None | None | POST endpoint for HITL resume (enables approval modal) |
| `messages` | list[AgentMessage] \| None | None | Initial messages |
| `placeholder` | str | `"メッセージを入力..."` | Input placeholder |
| `send_label` | str | `"送信"` | Submit button label |
| `stop_label` | str | `"停止"` | Stop button label (during streaming) |
| `agent_name` | str | `"Agent"` | Agent display name |
| `user_name` | str | `"You"` | User display name |
| `height` | str | `"700px"` | Container CSS height |
| `show_metrics` | bool | True | Show metrics bar |
| `show_status` | bool | True | Show status bar |
| `tool_expanded` | bool | False | Default tool panel state |
| `approve_label` | str | `"承認"` | Approve button label in interrupt modal |
| `reject_label` | str | `"拒否"` | Reject button label in interrupt modal |
| `agent_id` | str \| None | None | Auto-generated if omitted |

### Stop Button

During streaming, the send button automatically transforms into a stop button (red, with the `stop_label` text). Clicking it aborts the fetch request via `AbortController`, preserving any content received so far. The button reverts to the send state after stopping.

```python
AgentView(
    send_url="/api/agent",
    stop_label="Cancel",  # customize the stop button text
)
```

This feature is also available on `ChatView` with the same `stop_label` parameter.

## AgentEvent

Framework-agnostic SSE event for agent streaming. Works with any LLM framework (Anthropic, OpenAI, LangChain, etc.).

### Event Types

| Type | Fields | Description |
|------|--------|-------------|
| `"text"` | `content` | Streaming text token |
| `"tool_call"` | `call_id`, `tool_name`, `tool_input` | Tool invocation started |
| `"tool_result"` | `call_id`, `result` | Tool execution completed |
| `"status"` | `content` | Status bar update |
| `"plan"` | `content` | Task plan update (JSON, used by `DeepAgentView`) |
| `"interrupt"` | `content`, `tool_name`, `tool_input`, `metrics` | Human-in-the-loop approval request |
| `"error"` | `content` | Error message |
| `"done"` | `metrics` | Stream complete |

### Metrics

The `done` event can include a `metrics` dict with:

- `tokens` — Total tokens used
- `duration_ms` — Total execution time in milliseconds
- `tool_calls` — Number of tool calls made

## AgentMessage

A Pydantic BaseModel for initial messages with optional tool call history.

```python
from kokage_ui.ai import AgentMessage, ToolCall

# User message
msg = AgentMessage(role="user", content="Search for kokage-ui")

# Assistant message with tool calls
msg = AgentMessage(
    role="assistant",
    content="Here are the results...",
    tool_calls=[
        ToolCall(name="search", input={"q": "kokage-ui"}, result="Found 3 items", call_id="tc1"),
    ],
)
```

## FilePreview (Rich Tool Results)

Tool results are automatically rendered with rich previews based on content type detection. You can also provide a `preview_hint` to explicitly specify the format.

### Supported Types

| Type | Detection | Preview |
|------|-----------|---------|
| **JSON** | `{` or `[` prefix | Collapsible tree view |
| **CSV** | Consistent comma/tab columns | DaisyUI table |
| **Code** | `hint="python"` etc. | Syntax-highlighted block |
| **Image** | URL with image extension | `<img>` tag |
| **Text** | Fallback | `<pre>` block |

### Usage with AgentEvent

```python
# JSON result — auto-detected or hinted
yield AgentEvent(
    type="tool_result",
    call_id="tc1",
    result='[{"name": "Alice"}, {"name": "Bob"}]',
    preview_hint="json",
)

# CSV result
yield AgentEvent(
    type="tool_result",
    call_id="tc2",
    result="name,age\nAlice,30\nBob,25",
    preview_hint="csv",
)
```

### Standalone Component

`FilePreview` can also be used independently:

```python
from kokage_ui.ai import FilePreview

FilePreview('{"key": "value"}')                         # JSON tree
FilePreview("name,age\nAlice,30", hint="csv")            # Table
FilePreview("def hello(): pass", hint="python")          # Code
FilePreview(url="/uploads/image.png")                    # Image
```

## agent_stream

Converts an async `AgentEvent` generator to an SSE `StreamingResponse`.

```python
from kokage_ui.ai import AgentEvent, agent_stream

async def run():
    yield AgentEvent(type="status", content="Working...")
    yield AgentEvent(type="text", content="Hello ")
    yield AgentEvent(type="text", content="world!")
    yield AgentEvent(type="done", metrics={"tokens": 10})

return agent_stream(run())
```

SSE wire format:

```
data: {"type":"text","content":"Hello "}

data: {"type":"text","content":"world!"}

data: {"type":"done","metrics":{"tokens":10}}
```

## Framework Integration

### Anthropic Claude

```python
import anthropic
from kokage_ui.ai import AgentEvent, agent_stream

client = anthropic.AsyncAnthropic()

async def run(message: str):
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": message}],
        stream=True,
    )
    async for event in response:
        if event.type == "content_block_delta":
            yield AgentEvent(type="text", content=event.delta.text)
    yield AgentEvent(type="done")
```

### OpenAI

```python
from openai import AsyncOpenAI
from kokage_ui.ai import AgentEvent, agent_stream

client = AsyncOpenAI()

async def run(message: str):
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": message}],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield AgentEvent(type="text", content=delta.content)
    yield AgentEvent(type="done")
```

## UI Layout

```
┌──────────────────────────────────────────────┐
│ 🔄 Thinking...                               │  ← Status bar
├──────────────────────────────────────────────┤
│                                              │
│  [You]  Hello                                │
│                                              │
│  [Agent]                                     │
│  ┌─ 🔧 Tool  search()               [▼] ─┐  │
│  │  Input:  {"q": "foo"}                  │  │
│  │  Result: Found 3 items...              │  │
│  └────────────────────────────────────────┘  │
│  Based on the search results...              │
│                                              │
├──────────────────────────────────────────────┤
│ Tokens: 150  Duration: 2.5s  Tools: 1        │  ← Metrics bar
├──────────────────────────────────────────────┤
│ [メッセージを入力...]          [送信] / [停止] │
└──────────────────────────────────────────────┘
```

## Human-in-the-Loop (Interrupt)

AgentView supports human-in-the-loop approval via the `interrupt` event type. When an `interrupt` event is received and `interrupt_url` is set, the UI shows a DaisyUI modal with tool details and approve/reject buttons.

```python
AgentView(
    send_url="/api/agent",
    interrupt_url="/api/agent/resume",
    approve_label="Allow",
    reject_label="Deny",
)
```

The resume endpoint receives a JSON payload:

```json
{"decisions": [{"type": "approve"}]}
```

Decision types: `"approve"`, `"reject"`, or `"edit"` (with `"edited_action"` dict).

See [Deep Agents Integration](deepagents.md) for a complete HITL setup example.
