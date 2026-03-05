# kokage-ui

[![PyPI version](https://img.shields.io/pypi/v/kokage-ui)](https://pypi.org/project/kokage-ui/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-125%20passed-brightgreen)](#)

**Add beautiful UI to FastAPI with pure Python. No JavaScript, no templates, no frontend build step.**

<!-- TODO: Add screenshot/GIF of the dashboard example -->
<!-- <img src="docs/screenshot.png" alt="kokage-ui demo" width="800"> -->

## Quick Start

```python
# hello.py
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
pip install kokage-ui
uvicorn hello:app --reload
```

Open http://localhost:8000 — that's it.

## Why kokage-ui?

| | kokage-ui | Jinja2 Templates | Streamlit | NiceGUI |
|---|---|---|---|---|
| **Language** | Pure Python | Python + HTML | Python | Python |
| **Framework** | FastAPI | Any | Built-in | Built-in |
| **Routing** | FastAPI native | Manual | Automatic | Automatic |
| **API + UI** | Same app | Same app | Separate | Same app |
| **Component style** | DaisyUI / Tailwind | Custom CSS | Built-in widgets | Built-in widgets |
| **Real-time updates** | htmx (server-side) | WebSocket / polling | WebSocket | WebSocket |
| **Build step** | None | None | None | None |
| **Learning curve** | FastAPI + Python | HTML + Jinja2 | Streamlit API | NiceGUI API |

## Features

### 50+ HTML Elements

Every standard HTML element is available as a Python class. Underscores become hyphens, `cls` becomes `class`.

```python
from kokage_ui import Div, H1, P, A, Ul, Li, Input

# <div class="container" id="main">
#   <h1>Title</h1>
#   <a href="/about" hx-get="/about" hx-target="#content">About</a>
# </div>
Div(
    H1("Title"),
    A("About", href="/about", hx_get="/about", hx_target="#content"),
    cls="container", id="main",
)
```

### DaisyUI Components

High-level components that generate proper DaisyUI markup.

```python
from kokage_ui import Card, Hero, Stats, Stat, Alert, Badge, NavBar, DaisyButton

# Card with title, content, and actions
Card(
    P("Card content here"),
    title="My Card",
    actions=[DaisyButton("Click me", color="primary")],
)

# Stats dashboard
Stats(
    Stat(title="Users", value="2,100", desc="+21% this month"),
    Stat(title="Revenue", value="$45K", desc="+5% from last week"),
)

# Hero section
Hero(
    H1("Welcome", cls="text-5xl font-bold"),
    P("Build something amazing."),
    DaisyButton("Get Started", color="primary", size="lg"),
    min_height="60vh",
)

# Alerts and badges
Alert("Operation completed!", variant="success")
Badge("NEW", color="primary")
```

### Pydantic Model → UI

Auto-generate forms, tables, and detail views from Pydantic models. Field types are mapped to appropriate inputs — `bool` → checkbox, `Literal` → dropdown, `str` fields named `email` → email input.

```python
from pydantic import BaseModel, Field
from kokage_ui import ModelForm, ModelTable, ModelDetail

class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str
    age: int = Field(ge=0, le=150)
    is_active: bool = True

# Auto-generated form with validation attributes
ModelForm(User, action="/users", submit_text="Create User")

# Auto-generated table from a list of instances
ModelTable(User, rows=users, zebra=True)

# Auto-generated detail card
ModelDetail(user_instance)
```

### One-Line CRUD

Full list/create/detail/edit/delete UI from a single method call.

```python
from kokage_ui import KokageUI, InMemoryStorage

ui = KokageUI(app)

ui.crud(
    "/users",
    model=User,
    storage=InMemoryStorage(User, initial=seed_data),
    title="Users",
    form_exclude=["bio"],        # hide fields from forms
    page_wrapper=my_layout,      # wrap pages with your navbar/layout
)
# Generates: GET /users, GET /users/new, POST /users/new,
#             GET /users/{id}, GET /users/{id}/edit, POST /users/{id}/edit,
#             DELETE /users/{id}
```

### htmx Patterns

Common htmx patterns as Python components — no JavaScript required.

```python
from kokage_ui import AutoRefresh, SearchFilter, InfiniteScroll, ConfirmDelete

# Auto-refresh every 5 seconds
AutoRefresh(Span("Loading..."), url="/api/stats", interval=5)

# Live search with debounce
SearchFilter(url="/api/search", target="#results", placeholder="Search...")

# Infinite scroll
InfiniteScroll(url="/api/items?page=2", target="#item-list")

# Delete with confirmation dialog
ConfirmDelete("Delete", url="/api/items/1", confirm_message="Are you sure?")
```

### Pages & Fragments

Two decorators cover all routing needs.

```python
ui = KokageUI(app)

# Full HTML page (returns <!DOCTYPE html>)
@ui.page("/")
def index():
    return Page(Card(H1("Home")), title="Home")

# HTML fragment for htmx partial updates (htmx-only by default)
@ui.fragment("/api/widget")
def widget(request: Request):
    return Div(P("Updated content"), id="widget")
```

## Installation

```bash
pip install kokage-ui
# or
uv add kokage-ui
```

## Examples

| Example | Description | Run |
|---|---|---|
| [hello.py](examples/hello.py) | Minimal app — single card | `uvicorn examples.hello:app` |
| [todo.py](examples/todo.py) | CRUD todo app with navbar | `uvicorn examples.todo:app` |
| [dashboard.py](examples/dashboard.py) | Full dashboard: hero, stats, search, CRUD | `uvicorn examples.dashboard:app` |

## How It Works

kokage-ui follows the **server-side rendering + htmx** architecture:

1. **Python components** generate HTML strings on the server
2. **htmx** handles partial page updates without full reloads
3. **DaisyUI + Tailwind CSS** (loaded via CDN) provide styling
4. **FastAPI** handles routing and serves responses

```
Browser                    Server (FastAPI + kokage-ui)
   │                              │
   │──── GET / ───────────────────▶│  @ui.page("/") → Page(...)
   │◀─── Full HTML ───────────────│  → <!DOCTYPE html>...
   │                              │
   │──── htmx GET /api/stats ────▶│  @ui.fragment("/api/stats") → Stats(...)
   │◀─── HTML fragment ──────────│  → <div class="stats">...
```

No virtual DOM, no JavaScript bundler, no client-side state management. The server renders HTML, htmx swaps it into the page.

## API Quick Reference

| Module | Exports |
|---|---|
| **Core** | `KokageUI`, `Page`, `Component`, `Raw` |
| **HTML Elements** | `Div`, `Span`, `H1`–`H6`, `P`, `A`, `Img`, `Form`, `Input`, `Button`, `Table`, `Ul`, `Li`, ... (50+ elements) |
| **DaisyUI** | `Card`, `Hero`, `Stats`, `Stat`, `Alert`, `Badge`, `NavBar`, `DaisyButton`, `DaisyInput`, `DaisySelect`, `DaisyTextarea`, `DaisyTable` |
| **Model → UI** | `ModelForm`, `ModelTable`, `ModelDetail` |
| **htmx Patterns** | `AutoRefresh`, `SearchFilter`, `InfiniteScroll`, `SSEStream`, `ConfirmDelete`, `HxSwapOOB` |
| **CRUD** | `CRUDRouter`, `InMemoryStorage`, `Storage`, `Pagination` |

## Origin

kokage-ui was born from the Japanese FastAPI community. The original idea comes from [this article on Zenn](https://zenn.dev/livetoon/articles/04dccf642d324c) — combining FastAPI with htmx to build UI without leaving Python.

## License

MIT
