# Todo App

A complete CRUD application built with a single `ui.crud()` call.

## Full Code

```python
"""kokage-ui: Todo CRUD app."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from kokage_ui import A, InMemoryStorage, KokageUI, Layout, NavBar

app = FastAPI()
ui = KokageUI(app)


class Todo(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=200)
    completed: bool = False
    priority: Literal["low", "medium", "high"] = "medium"


INITIAL_TODOS = [
    Todo(id="1", title="Buy groceries", completed=False, priority="high"),
    Todo(id="2", title="Write documentation", completed=True, priority="medium"),
    Todo(id="3", title="Review pull requests", completed=False, priority="low"),
]

storage = InMemoryStorage(Todo, initial=INITIAL_TODOS)

layout = Layout(
    navbar=NavBar(
        start=A("Todo App", cls="btn btn-ghost text-xl", href="/todos"),
        end=A("New Todo", cls="btn btn-primary btn-sm", href="/todos/new"),
    ),
    title_suffix=" - Todo App",
    include_toast=True,
)

ui.crud(
    "/todos",
    model=Todo,
    storage=storage,
    title="Todos",
    layout=layout,
)
```

## Run

```bash
uv run uvicorn examples.todo:app --reload
```

Open [http://localhost:8000/todos](http://localhost:8000/todos).

## Walkthrough

### 1. Define the Model

```python
class Todo(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=200)
    completed: bool = False
    priority: Literal["low", "medium", "high"] = "medium"
```

- `id: str = ""` — Auto-assigned by `InMemoryStorage` if empty
- `title` — Required string with length validation (renders as `<input type="text">` with `minlength`/`maxlength`)
- `completed` — Boolean (renders as checkbox)
- `priority` — Literal type (renders as `<select>` dropdown)

### 2. Set Up Storage

```python
storage = InMemoryStorage(Todo, initial=INITIAL_TODOS)
```

`InMemoryStorage` provides an async dict-based store. Pass `initial` to seed data.

### 3. Configure Layout

```python
layout = Layout(
    navbar=NavBar(
        start=A("Todo App", cls="btn btn-ghost text-xl", href="/todos"),
        end=A("New Todo", cls="btn btn-primary btn-sm", href="/todos/new"),
    ),
    title_suffix=" - Todo App",
    include_toast=True,
)
```

`Layout` wraps every CRUD page with a consistent navbar and enables toast notifications for create/update/delete feedback.

### 4. Register CRUD Routes

```python
ui.crud("/todos", model=Todo, storage=storage, title="Todos", layout=layout)
```

This single line creates all CRUD routes:

- `GET /todos` — List with search and pagination
- `GET /todos/new` — Create form (title, completed checkbox, priority dropdown)
- `POST /todos/new` — Create handler with validation
- `GET /todos/{id}` — Detail view
- `GET /todos/{id}/edit` — Edit form with pre-filled values
- `POST /todos/{id}/edit` — Update handler
- `DELETE /todos/{id}` — Delete with confirmation
