# LangChain / LangGraph Integration

kokage-ui provides one-line adapters that convert LangChain and LangGraph streaming output directly into SSE `StreamingResponse` for use with `AgentView`.

Install the optional dependency:

```bash
pip install kokage-ui[langchain]
```

## langchain_agent_stream

Converts LangChain `astream_events` v2 output directly into `StreamingResponse`.

```python
from fastapi import FastAPI, Request
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from kokage_ui import KokageUI, Page
from kokage_ui.ai import AgentView
from kokage_ui.ai.langchain import langchain_agent_stream

app = FastAPI()
ui = KokageUI(app)

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

llm = ChatOpenAI(model="gpt-4o", streaming=True)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
agent = create_tool_calling_agent(llm, [search], prompt)
executor = AgentExecutor(agent=agent, tools=[search])

@ui.page("/")
def home():
    return Page(
        AgentView(send_url="/api/agent", agent_name="LangChain Agent"),
        title="LangChain Agent",
    )

@app.post("/api/agent")
async def run_agent(request: Request):
    data = await request.json()
    events = executor.astream_events(
        {"input": data["message"]}, version="v2"
    )
    return langchain_agent_stream(events)
```

### Event Mapping

| LangChain Event | AgentEvent |
|-----------------|------------|
| `on_chat_model_stream` | `text` (content from AIMessageChunk) |
| `on_tool_start` | `tool_call` + `status` |
| `on_tool_end` | `tool_result` |
| `on_chain_start` (agent) | `status` ("Thinking...") |
| `on_chain_end` (agent) | `done` |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `events` | AsyncIterator | (required) | Output from `astream_events(..., version="v2")` |
| `include_status` | bool | True | Emit status events on chain/tool start |

## langgraph_agent_stream

Converts LangGraph `astream` output directly into `StreamingResponse`. Supports `messages` and `updates` stream modes.

### Messages Mode (default)

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from kokage_ui.ai.langgraph import langgraph_agent_stream

llm = ChatOpenAI(model="gpt-4o", streaming=True)
agent = create_react_agent(llm, tools=[search])

@app.post("/api/agent")
async def run_agent(request: Request):
    data = await request.json()
    stream = agent.astream(
        {"messages": [("user", data["message"])]},
        stream_mode="messages",
    )
    return langgraph_agent_stream(stream)
```

### Updates Mode

```python
@app.post("/api/agent")
async def run_agent(request: Request):
    data = await request.json()
    stream = agent.astream(
        {"messages": [("user", data["message"])]},
        stream_mode="updates",
    )
    return langgraph_agent_stream(stream, stream_mode="updates")
```

### Event Mapping (messages mode)

| LangGraph Output | AgentEvent |
|-----------------|------------|
| `AIMessageChunk.content` | `text` |
| `AIMessageChunk.tool_calls` | `tool_call` |
| `ToolMessage` | `tool_result` |
| Node transition | `status` ("Running {node}...") |
| Stream end | `done` |

### Event Mapping (updates mode)

| LangGraph Output | AgentEvent |
|-----------------|------------|
| `AIMessage.content` | `text` |
| `AIMessage.tool_calls` | `tool_call` |
| `ToolMessage` | `tool_result` |
| Node output | `status` ("Completed {node}") |
| Stream end | `done` |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stream` | AsyncIterator | (required) | Output from `graph.astream(...)` |
| `stream_mode` | str | `"messages"` | Must match the mode passed to `astream()` |
| `include_status` | bool | True | Emit status events on node transitions |

## LangChainCallbackHandler

Callback-based adapter for `AgentExecutor` and other runnables that don't support `astream_events`. Implements LangChain's `AsyncCallbackHandler` and collects events into an async queue.

```python
import asyncio
from kokage_ui.ai import agent_stream
from kokage_ui.ai.langchain import LangChainCallbackHandler

handler = LangChainCallbackHandler()

@app.post("/api/agent")
async def run_agent(request: Request):
    data = await request.json()

    async def run():
        task = asyncio.create_task(
            executor.ainvoke(
                {"input": data["message"]},
                config={"callbacks": [handler]},
            )
        )
        async for event in handler.events():
            yield event
        await task

    return agent_stream(run())
```

### Callback Mapping

| LangChain Callback | AgentEvent |
|--------------------|------------|
| `on_llm_new_token` | `text` |
| `on_tool_start` | `tool_call` + `status` |
| `on_tool_end` | `tool_result` |
| `on_tool_error` | `error` |
| `on_chain_start` (agent) | `status` ("Thinking...") |
| `on_chain_error` | `error` |
| `on_llm_error` | `error` |
| `handler.finish()` | `done` (with optional metrics) |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_status` | bool | True | Emit status events on chain/tool start |

### Methods

| Method | Description |
|--------|-------------|
| `events()` | Async iterator yielding `AgentEvent` until `finish()` is called |
| `finish(metrics=None)` | Signal completion and emit `done` event |

## ToolRegistry

A decorator-based registry for defining tools. Works standalone and can be converted to LangChain tools via `to_langchain_tools`.

```python
from kokage_ui.ai.tools import ToolRegistry

registry = ToolRegistry()

@registry.tool
async def search(query: str, limit: int = 5) -> str:
    """Search the database for matching records."""
    return f"Found results for: {query}"

@registry.tool(name="calculate", description="Evaluate a math expression")
def calc(expression: str) -> str:
    return str(eval(expression))

# List registered tools
for info in registry.list():
    print(info.name, info.description, info.parameters)
```

### ToolInfo

Each registered tool produces a `ToolInfo` with:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Tool name |
| `description` | str | From docstring or override |
| `parameters` | dict | JSON Schema from type hints |
| `func` | Callable | The original function |
| `is_async` | bool (property) | Whether the function is async |

### ToolInfo.ainvoke

Call the tool, awaiting if async:

```python
info = registry.get("search")
result = await info.ainvoke(query="kokage-ui", limit=3)
```

## to_langchain_tools

Converts tools to LangChain `StructuredTool` instances. Accepts a `ToolRegistry`, a list of `ToolInfo`, or a list of plain callables.

```python
from kokage_ui.ai.langchain import to_langchain_tools

# From ToolRegistry
lc_tools = to_langchain_tools(registry)

# From plain functions
def greet(name: str) -> str:
    """Say hello."""
    return f"Hello {name}"

lc_tools = to_langchain_tools([greet])

# Use with LangChain agent
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(llm, lc_tools)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | ToolRegistry / list[ToolInfo] / list[Callable] | (required) | Tools to convert |
| `handle_errors` | bool | True | Return errors as strings instead of raising |
