# Deep Agents Demo

Demonstrates the Deep Agents integration with kokage-ui, including the plan sidebar, file activity tracking, and human-in-the-loop approval flow.

## Run

```bash
pip install kokage-ui[deepagents]

# Plan visualization demo (mock, no LLM needed)
uvicorn examples.deepagents_plan_demo:app --reload

# Basic streaming demo (mock)
uvicorn examples.deepagents_demo:app --reload

# HITL interrupt demo (mock)
uvicorn examples.deepagents_hitl_demo:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Demos

### Plan Demo (`deepagents_plan_demo`)

Shows `DeepAgentView` with the right-side plan sidebar:

- Task plan updates in real-time as the agent calls `write_todos`
- Status icons show progress: ⬜ pending → 🔄 in-progress → ✅ completed
- File activity tracks `ls`, `read_file`, `write_file` tool calls

### Basic Demo (`deepagents_demo`)

Shows basic Deep Agents streaming with `AgentView`:

- `write_todos` for task planning
- `read_file` with file content preview
- Streaming text response

### HITL Demo (`deepagents_hitl_demo`)

Shows the human-in-the-loop interrupt flow:

- Agent attempts a `delete_file` tool call
- Execution pauses and shows an approval modal
- User can approve (continues) or reject (stops)

## Source

::: examples.deepagents_plan_demo
