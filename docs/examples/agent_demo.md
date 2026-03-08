# Agent Demo

An interactive AI agent dashboard demonstrating tool call visualization, status updates, and metrics display.

## Run

```bash
uv run uvicorn examples.agent_demo:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Features

- **Status bar** — Shows agent thinking state ("考え中...", "回答を生成中...")
- **Tool call panels** — Collapsible panels showing tool input/output with spinner during execution
- **Streaming text** — Markdown-rendered response streamed token by token
- **Metrics bar** — Token count, duration, and tool call count after completion
- **Chat history** — DaisyUI chat bubbles for user and agent messages

## How It Works

1. User sends a message via the input form
2. Agent shows "考え中..." status
3. Agent calls `search` tool with the user's query
4. Tool result is displayed in a collapsible panel
5. Agent streams a Markdown-formatted response
6. Metrics (tokens, duration, tool calls) are shown at the bottom

## Source

::: details Full source code

```python
--8<-- "examples/agent_demo.py"
```

:::
