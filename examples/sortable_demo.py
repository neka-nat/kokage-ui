"""Sortable drag & drop demo.

Run:
    uv run uvicorn examples.sortable_demo:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from kokage_ui import (
    CRUDRouter,
    Div,
    H1,
    H2,
    InMemoryStorage,
    KokageUI,
    Page,
    SortableList,
)

app = FastAPI()
ui = KokageUI(app)


# ========================================
# Standalone SortableList
# ========================================


@ui.page("/")
def index():
    items = [
        {"id": "1", "label": "Learn Python", "badge": "High"},
        {"id": "2", "label": "Build a web app", "badge": "Medium"},
        {"id": "3", "label": "Write tests", "badge": "Low"},
        {"id": "4", "label": "Deploy to production"},
        {"id": "5", "label": "Monitor logs"},
    ]

    return Page(
        Div(
            H1("Sortable Demo", cls="text-3xl font-bold mb-6"),
            H2("Standalone SortableList", cls="text-xl font-semibold mb-4"),
            SortableList(items=items, url="/api/reorder"),
            H2(
                "CRUD with sortable=True",
                cls="text-xl font-semibold mt-8 mb-4",
            ),
            Div(
                "Visit ",
                Div("→ /tasks", cls="inline font-mono text-primary"),
                " for CRUD-integrated sortable list.",
            ),
            cls="container mx-auto p-4",
        ),
        title="Sortable Demo",
        include_sortablejs=True,
    )


@app.post("/api/reorder")
async def standalone_reorder():
    """Standalone reorder endpoint (no-op for demo)."""
    return {"ok": True}


# ========================================
# CRUD-integrated sortable
# ========================================


class Task(BaseModel):
    id: str = ""
    title: str = ""
    priority: str = "Medium"


storage = InMemoryStorage(
    Task,
    initial=[
        Task(id="1", title="Design database schema", priority="High"),
        Task(id="2", title="Implement API endpoints", priority="High"),
        Task(id="3", title="Write unit tests", priority="Medium"),
        Task(id="4", title="Set up CI/CD", priority="Medium"),
        Task(id="5", title="Update documentation", priority="Low"),
    ],
)

CRUDRouter(app, "/tasks", Task, storage, sortable=True, title="Tasks")
