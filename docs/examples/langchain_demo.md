# LangChain Demo

Demonstrates three LangChain/LangGraph integration patterns with kokage-ui's AgentView.

## Run

```bash
pip install kokage-ui[langchain]
uvicorn examples.langchain_demo:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Pages

| Path | Adapter | Description |
|------|---------|-------------|
| `/` | `langchain_stream` | Converts LangChain `astream_events` v2 to AgentEvent |
| `/langgraph` | `langgraph_stream` | Converts LangGraph `astream` (messages mode) to AgentEvent |
| `/callback` | `LangChainCallbackHandler` | Callback-based adapter for legacy `AgentExecutor` |

## ToolRegistry

The demo defines tools with `ToolRegistry` — a decorator-based registry that works standalone and can be converted to LangChain tools via `to_langchain_tools()`.

```python
from kokage_ui.ai import ToolRegistry

registry = ToolRegistry()

@registry.tool
async def search(query: str, limit: int = 3) -> str:
    """Search the knowledge base."""
    ...
```

## Source

::: examples.langchain_demo
