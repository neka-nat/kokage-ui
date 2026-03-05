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

## Documentation

For detailed guides, component reference, and API docs, see the [full documentation](https://neka-nat.github.io/kokage-ui/).

## License

MIT
