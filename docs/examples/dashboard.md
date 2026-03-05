# Dashboard

A feature-rich dashboard demonstrating CRUD, live stats, and search.

## Full Code

```python
"""kokage-ui sample: Dashboard application."""

import enum
import random
from typing import Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from kokage_ui import (
    A, Alert, AutoRefresh, Card, DaisyButton, DaisyTable,
    Div, Form, H1, H2, Hero, InMemoryStorage, KokageUI,
    ModelDetail, ModelForm, ModelTable, NavBar, P, Page,
    SearchFilter, Span, Stat, Stats,
)

app = FastAPI()
ui = KokageUI(app)


class Role(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(BaseModel):
    id: str = ""
    name: str = Field(min_length=1, max_length=100)
    email: str
    age: int = Field(ge=0, le=150, default=30)
    role: Role = Role.VIEWER
    is_active: bool = True
    bio: str = Field(default="", max_length=500)


INITIAL_USERS = [
    User(id="1", name="Tanaka Taro", email="tanaka@example.com",
         age=35, role=Role.ADMIN, is_active=True, bio="System administrator"),
    User(id="2", name="Suzuki Hanako", email="suzuki@example.com",
         age=28, role=Role.EDITOR, is_active=True),
    # ... more users
]

USERS_DICT = [
    {"name": u.name, "email": u.email, "role": u.role.value.title()}
    for u in INITIAL_USERS
]

storage = InMemoryStorage(User, initial=INITIAL_USERS)


def _navbar():
    return NavBar(
        start=A("kokage Dashboard", cls="btn btn-ghost text-xl", href="/"),
        end=Div(
            A("Home", cls="btn btn-ghost", href="/"),
            A("Users", cls="btn btn-ghost", href="/users"),
            A("New User", cls="btn btn-ghost", href="/users/new"),
        ),
    )


def _page_wrapper(content, title):
    return Page(
        _navbar(), content,
        title=f"{title} - kokage Dashboard", theme="light",
    )


# CRUD for User model
ui.crud(
    "/users", model=User, storage=storage,
    title="Users", form_exclude=["bio"],
    page_wrapper=_page_wrapper,
)


@ui.page("/")
def index():
    return Page(
        _navbar(),
        Div(
            Hero(
                H1("kokage-ui Demo", cls="text-5xl font-bold"),
                P("FastAPI + htmx + DaisyUI", cls="py-4 text-lg"),
                DaisyButton("Get Started", color="primary", size="lg"),
                min_height="50vh",
            ),
            H2("Live Stats (auto-refresh every 3s)",
               cls="text-2xl font-bold mt-8 mb-4 px-4"),
            AutoRefresh(
                Span("Loading...", cls="loading loading-spinner"),
                url="/api/stats", interval=3,
            ),
            H2("User Search", cls="text-2xl font-bold mt-8 mb-4 px-4"),
            Div(
                SearchFilter(
                    url="/api/users/search", target="#user-table",
                    placeholder="Search users...",
                ),
                cls="px-4 mb-4",
            ),
            Div(id="user-table"),
            cls="container mx-auto",
        ),
        title="kokage Dashboard", theme="light",
    )


@ui.fragment("/api/stats")
def live_stats(request: Request):
    return Stats(
        Stat(title="Active Users", value=str(random.randint(80, 150))),
        Stat(title="Requests/s", value=f"{random.randint(100, 500):,}"),
        Stat(title="CPU Usage", value=f"{random.randint(20, 80)}%"),
        Stat(title="Memory", value=f"{random.randint(40, 90)}%"),
    )


@ui.fragment("/api/users/search")
def search_users(request: Request, q: str = ""):
    filtered = (
        [u for u in USERS_DICT if q.lower() in u["name"].lower()]
        if q else USERS_DICT
    )
    return DaisyTable(
        headers=["Name", "Email", "Role"],
        rows=[[u["name"], u["email"], u["role"]] for u in filtered],
        zebra=True,
    )
```

## Run

```bash
uv run uvicorn examples.dashboard:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

## Key Patterns

### Hero Section

The landing page uses `Hero` for a prominent banner:

```python
Hero(
    H1("kokage-ui Demo", cls="text-5xl font-bold"),
    P("FastAPI + htmx + DaisyUI", cls="py-4 text-lg"),
    DaisyButton("Get Started", color="primary", size="lg"),
    min_height="50vh",
)
```

### Live Auto-Refreshing Stats

`AutoRefresh` polls `/api/stats` every 3 seconds, and the `@ui.fragment` endpoint returns a `Stats` component with random values:

```python
AutoRefresh(
    Span("Loading..."),
    url="/api/stats",
    interval=3,
)
```

### Live Search

`SearchFilter` sends debounced keyup events to `/api/users/search`, which filters and returns a `DaisyTable`:

```python
SearchFilter(
    url="/api/users/search",
    target="#user-table",
    placeholder="Search users...",
)
```

### CRUD with Custom page_wrapper

Instead of using `Layout`, this example defines a custom `_page_wrapper` function to wrap CRUD pages with a navbar:

```python
def _page_wrapper(content, title):
    return Page(_navbar(), content, title=f"{title} - kokage Dashboard")

ui.crud("/users", model=User, storage=storage, page_wrapper=_page_wrapper)
```

### Enum Fields

The `Role` enum automatically renders as a `<select>` dropdown in forms, with options derived from enum members.
