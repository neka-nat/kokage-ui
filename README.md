![logo](assets/logo.svg)

[![PyPI version](https://img.shields.io/pypi/v/kokage-ui)](https://pypi.org/project/kokage-ui/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Add beautiful UI to FastAPI with pure Python. No JavaScript, no templates, no frontend build step.**

## Quick Start

```bash
pip install kokage-ui
```

```python
from fastapi import FastAPI
from kokage_ui import KokageUI, Page, Card, H1, P, DaisyButton

app = FastAPI()
ui = KokageUI(app)

@ui.page("/")
def home():
    return Page(
        Card(
            H1("Hello, World!"),
            P("Built with FastAPI + htmx + DaisyUI. Pure Python."),
            actions=[DaisyButton("Get Started", color="primary")],
            title="Welcome to kokage-ui",
        ),
        title="Hello App",
    )
```

```bash
uvicorn hello:app --reload
```

Please open [http://localhost:8000](http://localhost:8000) in your browser.

![](assets/hello_world.png)


## CRUD in 10 Lines

Define a Pydantic model and get full CRUD UI automatically:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from kokage_ui import KokageUI, InMemoryStorage

app = FastAPI()
ui = KokageUI(app)

class Todo(BaseModel):
    id: str = ""
    title: str = Field(min_length=1)
    done: bool = False

ui.crud("/todos", model=Todo, storage=InMemoryStorage(Todo))
```

This single `ui.crud()` call generates list, create, detail, edit, and delete pages with search and pagination — all styled with DaisyUI.

https://github.com/user-attachments/assets/4c4ad3be-664d-432e-9c2e-23e80755b461

## Streaming Chat UI

Build an LLM chat interface with SSE streaming in a few lines:

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
        async for token in your_llm(data["message"]):  # OpenAI, Anthropic, etc.
            yield token

    return chat_stream(generate())
```

`ChatView` renders DaisyUI chat bubbles with real-time SSE streaming, Markdown rendering, and code highlighting.

## Features

- **50+ HTML Elements** — `Div`, `H1`, `Form`, `Input`, etc. as Python classes
- **25+ DaisyUI Components** — `Card`, `Hero`, `NavBar`, `Modal`, `Tabs`, `Accordion`, `Toast`, `Layout`, and more
- **Pydantic → UI** — Auto-generate forms, tables, detail views from `BaseModel`
- **One-line CRUD** — `ui.crud("/users", model=User, storage=storage)`
- **DataGrid** — Sortable, filterable table with pagination, bulk actions, CSV export
- **Admin Dashboard** — Django-like admin panel: `AdminSite(app).register(User, storage=s)`
- **Auth UI** — `LoginForm`, `RegisterForm`, `UserMenu`, `RoleGuard`, `@protected` decorator
- **Theme System** — `DarkModeToggle` and `ThemeSwitcher` with localStorage persistence
- **Real-time Notifications** — SSE-based push notifications via `Notifier` + `NotificationStream`
- **SQLModel Storage** — Async database persistence with `SQLModelStorage`
- **htmx Patterns** — `AutoRefresh`, `SearchFilter`, `InfiniteScroll`, `SSEStream`, `ConfirmDelete`
- **Charts & Markdown** — `Chart` (Chart.js), `CodeBlock` (Highlight.js), `Markdown`
- **Multi-step Forms** — `MultiStepForm` with step validation
- **CLI Scaffolding** — `kokage-ui init myapp` to generate project templates
- **XSS Protection** — Output escaped via `markupsafe` by default

## CLI

```bash
uvx kokage-ui init myapp            # Create new project
uvx kokage-ui init myapp --crud     # Create with CRUD template
uvx kokage-ui add page dashboard    # Add a new page
uvx kokage-ui add crud Product      # Add CRUD model
```

## Examples

| Example | Description | Run |
|---|---|---|
| [hello.py](examples/hello.py) | Minimal app | `uvicorn examples.hello:app` |
| [todo.py](examples/todo.py) | CRUD todo app | `uvicorn examples.todo:app` |
| [dashboard.py](examples/dashboard.py) | Full dashboard | `uvicorn examples.dashboard:app` |
| [admin_demo.py](examples/admin_demo.py) | Admin panel + Auth | `uvicorn examples.admin_demo:app` |
| [blog.py](examples/blog.py) | Markdown + Charts + Tabs | `uvicorn examples.blog:app` |
| [realtime.py](examples/realtime.py) | SSE notifications | `uvicorn examples.realtime:app` |
| [chat_demo.py](examples/chat_demo.py) | Streaming chat UI | `uvicorn examples.chat_demo:app` |

## Documentation

For detailed guides, component reference, and API docs, see the [full documentation](https://neka-nat.github.io/kokage-ui/).

## License

MIT
