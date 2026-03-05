"""kokage-ui: Todo CRUD app.

Run:
    uv run uvicorn examples.todo:app --reload

Open http://localhost:8000/todos in your browser.
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from kokage_ui import A, InMemoryStorage, KokageUI, NavBar, Page

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


def _navbar():
    return NavBar(
        start=A("Todo App", cls="btn btn-ghost text-xl", href="/todos"),
        end=A("New Todo", cls="btn btn-primary btn-sm", href="/todos/new"),
    )


def page_wrapper(content, title):
    return Page(
        _navbar(),
        content,
        title=f"{title} - Todo App",
    )


ui.crud(
    "/todos",
    model=Todo,
    storage=storage,
    title="Todos",
    page_wrapper=page_wrapper,
)
