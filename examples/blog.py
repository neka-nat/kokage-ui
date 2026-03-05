"""kokage-ui: Blog app with Markdown, Charts, and Tabs.

Run:
    uv run uvicorn examples.blog:app --reload

Open http://localhost:8000 in your browser.

Features demonstrated:
    - Markdown rendering
    - CodeBlock (syntax highlighting)
    - Chart (Chart.js)
    - Tabs (content mode)
    - Card, Badge, Breadcrumb
    - NavBar with ThemeSwitcher
"""

from fastapi import FastAPI, Request

from kokage_ui import (
    A,
    Badge,
    Breadcrumb,
    Card,
    Chart,
    CodeBlock,
    DarkModeToggle,
    Div,
    H1,
    H2,
    KokageUI,
    Markdown,
    NavBar,
    P,
    Page,
    Span,
    Tab,
    Tabs,
    ThemeSwitcher,
)

app = FastAPI()
ui = KokageUI(app)

# ---------- Blog Data ----------

POSTS = {
    "getting-started": {
        "title": "Getting Started with kokage-ui",
        "date": "2025-12-01",
        "tags": ["tutorial", "python"],
        "content": """\
# Getting Started with kokage-ui

kokage-ui lets you build **interactive web UIs** entirely in Python.

## Installation

```bash
pip install kokage-ui
```

## Your First App

```python
from fastapi import FastAPI
from kokage_ui import KokageUI, Page, Card, H1

app = FastAPI()
ui = KokageUI(app)

@ui.page("/")
def home():
    return Page(Card(H1("Hello!"), title="Welcome"))
```

## Key Features

- **No JavaScript** required
- **DaisyUI** components built-in
- **htmx** for interactivity
- Full **Pydantic** integration

> kokage-ui makes FastAPI UI development a breeze!
""",
    },
    "htmx-patterns": {
        "title": "htmx Patterns in kokage-ui",
        "date": "2025-12-15",
        "tags": ["htmx", "advanced"],
        "content": """\
# htmx Patterns in kokage-ui

htmx powers the interactive features of kokage-ui.

## AutoRefresh

Poll a URL at a regular interval:

```python
AutoRefresh(
    Span("Loading..."),
    url="/api/stats",
    interval=3,
)
```

## SearchFilter

Debounced search input:

```python
SearchFilter(
    url="/api/search",
    target="#results",
    placeholder="Search...",
)
```

## Key Concepts

| Pattern | Trigger | Use Case |
|---------|---------|----------|
| AutoRefresh | `every Ns` | Live dashboards |
| SearchFilter | `keyup delay` | Search-as-you-type |
| InfiniteScroll | `revealed` | Paginated feeds |
| SSEStream | Server push | Real-time updates |
""",
    },
    "crud-tutorial": {
        "title": "One-line CRUD with kokage-ui",
        "date": "2026-01-10",
        "tags": ["tutorial", "crud"],
        "content": """\
# One-line CRUD with kokage-ui

Generate a full CRUD interface from a Pydantic model.

## Define Your Model

```python
from pydantic import BaseModel, Field

class Todo(BaseModel):
    id: str = ""
    title: str = Field(min_length=1)
    completed: bool = False
```

## Register CRUD

```python
from kokage_ui import InMemoryStorage

storage = InMemoryStorage(Todo)
ui.crud("/todos", model=Todo, storage=storage)
```

This creates **list**, **create**, **detail**, **edit**, and **delete** pages automatically.

## SQL Storage

For production, use `SQLModelStorage`:

```python
from kokage_ui import SQLModelStorage
storage = SQLModelStorage(Todo, engine)
```
""",
    },
}


# ---------- Layout ----------


def _navbar():
    return NavBar(
        start=A("kokage Blog", cls="btn btn-ghost text-xl", href="/"),
        end=Div(
            A("Posts", cls="btn btn-ghost btn-sm", href="/"),
            A("Stats", cls="btn btn-ghost btn-sm", href="/stats"),
            DarkModeToggle(),
            ThemeSwitcher(
                themes=["light", "dark", "nord", "dracula", "corporate"],
                size="sm",
            ),
            cls="flex items-center gap-2",
        ),
    )


def _page(content, title, breadcrumb_items=None):
    bc = Breadcrumb(items=[("Blog", "/")] + (breadcrumb_items or []))
    return Page(
        _navbar(),
        Div(bc, content, cls="container mx-auto p-6"),
        title=f"{title} - kokage Blog",
        include_chartjs=True,
        include_highlightjs=True,
    )


# ---------- Routes ----------


@ui.page("/")
def index():
    cards = []
    for slug, post in POSTS.items():
        tags = Div(
            *[Badge(tag, color="primary", cls="badge-sm") for tag in post["tags"]],
            cls="flex gap-1",
        )
        cards.append(
            Card(
                P(post["date"], cls="text-sm text-base-content/60"),
                tags,
                actions=[A("Read", href=f"/posts/{slug}", cls="btn btn-primary btn-sm")],
                title=post["title"],
            )
        )

    return _page(
        Div(
            H1("Blog Posts", cls="text-3xl font-bold mb-6"),
            Div(*cards, cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"),
        ),
        title="Posts",
    )


@ui.page("/posts/{slug}")
def post_page(slug: str):
    post = POSTS.get(slug)
    if post is None:
        return _page(
            Card(H1("Post not found"), title="404"),
            title="Not Found",
        )

    tags = Div(
        *[Badge(tag, color="primary") for tag in post["tags"]],
        cls="flex gap-1 mb-4",
    )

    # Tabbed view: rendered article + raw markdown source
    tabs = Tabs(
        tabs=[
            Tab(
                label="Article",
                content=Div(
                    tags,
                    P(post["date"], cls="text-sm text-base-content/60 mb-4"),
                    Markdown(post["content"]),
                ),
                active=True,
            ),
            Tab(
                label="Source",
                content=CodeBlock(post["content"], language="markdown"),
            ),
        ],
        variant="lifted",
    )

    return _page(
        tabs,
        title=post["title"],
        breadcrumb_items=[(post["title"], None)],
    )


@ui.page("/stats")
def stats_page():
    # Post statistics chart
    post_chart = Chart(
        type="bar",
        data={
            "labels": [p["title"][:20] + "..." for p in POSTS.values()],
            "datasets": [
                {
                    "label": "Word Count",
                    "data": [len(p["content"].split()) for p in POSTS.values()],
                    "backgroundColor": ["#36a2eb", "#ff6384", "#4bc0c0"],
                }
            ],
        },
        options={"plugins": {"title": {"display": True, "text": "Word Count per Post"}}},
        height="300px",
    )

    tag_counts: dict[str, int] = {}
    for post in POSTS.values():
        for tag in post["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    tag_chart = Chart(
        type="doughnut",
        data={
            "labels": list(tag_counts.keys()),
            "datasets": [
                {
                    "data": list(tag_counts.values()),
                    "backgroundColor": ["#ff6384", "#36a2eb", "#ffce56", "#4bc0c0"],
                }
            ],
        },
        options={"plugins": {"title": {"display": True, "text": "Posts by Tag"}}},
        height="300px",
    )

    # Timeline chart
    timeline_chart = Chart(
        type="line",
        data={
            "labels": sorted(p["date"] for p in POSTS.values()),
            "datasets": [
                {
                    "label": "Cumulative Posts",
                    "data": list(range(1, len(POSTS) + 1)),
                    "borderColor": "#36a2eb",
                    "fill": False,
                }
            ],
        },
        options={"plugins": {"title": {"display": True, "text": "Publishing Timeline"}}},
        height="300px",
    )

    return _page(
        Div(
            H1("Blog Statistics", cls="text-3xl font-bold mb-6"),
            Div(
                Card(post_chart, title="Word Count"),
                Card(tag_chart, title="Tag Distribution"),
                Card(timeline_chart, title="Timeline"),
                cls="grid grid-cols-1 lg:grid-cols-2 gap-6",
            ),
        ),
        title="Stats",
        breadcrumb_items=[("Stats", None)],
    )
