# Deep Agents Integration

kokage-ui provides a one-line adapter for [Deep Agents](https://github.com/langchain-ai/deepagents) — a LangGraph-based agent harness with built-in planning, filesystem, and sub-agent tools.

Install the optional dependency:

```bash
pip install kokage-ui[deepagents]
```

## Quick Start

```python
from fastapi import FastAPI, Request
from deepagents import create_deep_agent
from kokage_ui import KokageUI, Page
from kokage_ui.ai import AgentView
from kokage_ui.ai.deepagents import deep_agent_stream

app = FastAPI()
ui = KokageUI(app)

agent = create_deep_agent(
    tools=[my_tool],
    system_prompt="You are a helpful assistant",
)

@ui.page("/")
def home():
    return Page(
        AgentView(send_url="/api/agent", agent_name="Deep Agent"),
        title="Deep Agent",
        include_marked=True,
    )

@app.post("/api/agent")
async def run(request: Request):
    data = await request.json()
    return deep_agent_stream(agent, data["message"])
```

## deep_agent_stream

Converts a Deep Agent compiled graph into an SSE `StreamingResponse` for use with `AgentView` or `DeepAgentView`.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent` | CompiledStateGraph | (required) | Graph from `create_deep_agent()` |
| `message` | str | (required) | User message |
| `thread_id` | str \| None | None | Thread ID for conversation persistence (requires checkpointer) |
| `config` | DeepAgentConfig \| None | None | Adapter configuration |
| `extra_config` | dict \| None | None | Additional LangGraph config |

### Event Mapping

| Deep Agents Output | AgentEvent |
|-------------------|------------|
| `AIMessageChunk.content` | `text` |
| `AIMessageChunk.tool_calls` | `tool_call` |
| `ToolMessage` | `tool_result` |
| `ToolMessage` (write_todos) | `plan` (JSON todo list) + `tool_result` |
| Node transition | `status` ("Running {node}...") |
| Interrupt detected | `interrupt` |
| Stream end | `done` (with metrics) |

### DeepAgentConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include_status` | bool | True | Emit status events on node transitions |
| `include_plan` | bool | True | Emit `plan` events when `write_todos` is called |
| `include_metrics` | bool | True | Collect and emit execution metrics in done event |
| `stream_mode` | str | `"messages"` | LangGraph stream mode — `"messages"` or `"updates"` |

## Conversation Persistence

Use a LangGraph checkpointer for multi-turn conversations:

```python
from langgraph.checkpoint.memory import MemorySaver

agent = create_deep_agent(
    tools=[my_tool],
    checkpointer=MemorySaver(),
)

@app.post("/api/agent")
async def run(request: Request):
    data = await request.json()
    return deep_agent_stream(
        agent,
        data["message"],
        thread_id=data.get("thread_id", "default"),
    )
```

## Human-in-the-Loop (Interrupt)

Deep Agents supports interrupting execution for human approval of dangerous tool calls. kokage-ui renders an approval modal when an interrupt is detected.

### Setup

```python
agent = create_deep_agent(
    tools=[delete_file, send_email],
    interrupt_on={"delete_file": True, "send_email": True},
    checkpointer=MemorySaver(),
)
```

### Endpoints

```python
@app.post("/api/agent")
async def run(request: Request):
    data = await request.json()
    return deep_agent_stream(
        agent, data["message"], thread_id="session-1",
    )

@app.post("/api/agent/resume")
async def resume(request: Request):
    data = await request.json()
    return deep_agent_resume(
        agent,
        decisions=data["decisions"],
        thread_id="session-1",
    )
```

### UI

Pass `interrupt_url` to `AgentView` or `DeepAgentView` to enable the approval modal:

```python
AgentView(
    send_url="/api/agent",
    interrupt_url="/api/agent/resume",
    approve_label="承認",
    reject_label="拒否",
)
```

When the agent hits an interrupt, the UI shows a modal with tool details and approve/reject buttons. Chained interrupts (multiple approvals in sequence) are supported.

### deep_agent_resume

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent` | CompiledStateGraph | (required) | Same graph used in `deep_agent_stream()` |
| `decisions` | list[dict] | (required) | Decision dicts: `{"type": "approve"}`, `{"type": "reject"}`, or `{"type": "edit", "edited_action": {...}}` |
| `thread_id` | str | (required) | Thread ID from the interrupt event |
| `config` | DeepAgentConfig \| None | None | Adapter configuration |
| `extra_config` | dict \| None | None | Additional LangGraph config |

## DeepAgentView (Plan Sidebar)

`DeepAgentView` extends the agent dashboard with a right-side sidebar showing:

- **Task Plan** — Real-time visualization of the agent's plan from `write_todos` calls, with status icons per task
- **File Activity** — Tracks filesystem tool calls (read_file, write_file, edit_file, ls, glob, grep)

```python
from kokage_ui.ai.deepagent_view import DeepAgentView

@ui.page("/")
def home():
    return Page(
        DeepAgentView(
            send_url="/api/agent",
            interrupt_url="/api/agent/resume",
            agent_name="Deep Agent",
            plan_label="Task Plan",
            files_label="File Activity",
        ),
        title="Deep Agent",
        include_marked=True,
        include_highlightjs=True,
    )
```

### Parameters

All `AgentView` parameters are supported, plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_plan` | bool | True | Show task plan in sidebar |
| `show_files` | bool | True | Show file activity in sidebar |
| `plan_label` | str | `"Task Plan"` | Plan section heading |
| `files_label` | str | `"File Activity"` | File activity section heading |

### Plan Events

The plan sidebar updates from `plan` SSE events, which `deep_agent_stream` emits automatically when the agent calls `write_todos`. The event content is a JSON array of todo objects:

```json
[
  {"task": "Analyze project structure", "status": "completed"},
  {"task": "Read configuration files", "status": "in_progress"},
  {"task": "Implement feature", "status": "pending"}
]
```

Status icons:

| Status | Icon |
|--------|------|
| `pending` | ⬜ |
| `in_progress` / `running` | 🔄 |
| `completed` / `done` | ✅ |

### UI Layout

```
┌──────────────────────────────────┬────────────────┐
│ 🔄 Running agent...             │  Task Plan     │
├──────────────────────────────────│                │
│                                  │  ✅ Analyze    │
│  [You]  Fix the login bug        │  🔄 Read conf  │
│                                  │  ⬜ Implement  │
│  [Agent]                         │  ⬜ Test       │
│  ┌─ 🔧 read_file()        [▼] ─┐│                │
│  │  Input:  {"path":"conf.yaml"}││  File Activity │
│  │  Result: db: localhost       ││  ──────────────│
│  └──────────────────────────────┘│  👁 conf.yaml  │
│  Reading the configuration...    │  ✏️ feature.py  │
│                                  │                │
├──────────────────────────────────│                │
│ Duration: 5.0s  Tools: 3        │                │
├──────────────────────────────────┤                │
│ [メッセージを入力...]    [送信]   │                │
└──────────────────────────────────┴────────────────┘
```

## ToolRegistry Integration

Convert kokage-ui tools to Deep Agents format:

```python
from kokage_ui.ai import ToolRegistry
from kokage_ui.ai.deepagents import to_deep_agent_tools

registry = ToolRegistry()

@registry.tool
async def search(query: str) -> str:
    """Search the database."""
    return "results"

agent = create_deep_agent(tools=to_deep_agent_tools(registry))
```

## Filesystem Tool Previews

Deep Agents' built-in filesystem tools (`read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`) automatically get rich previews in the tool result panel. The adapter detects file extensions and content types:

| Extension | Preview |
|-----------|---------|
| `.json` | Collapsible JSON tree |
| `.csv`, `.tsv` | DaisyUI table |
| `.py`, `.js`, `.ts`, etc. | Syntax-highlighted code |
| `.png`, `.jpg`, `.svg` | Image |
| `.yaml`, `.toml`, `.md` | Formatted content |
