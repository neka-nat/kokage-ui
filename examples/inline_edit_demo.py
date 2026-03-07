"""Inline editing demo — click table cells to edit in place."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from kokage_ui import Div, H1, KokageUI, Page
from kokage_ui.components import Card, DaisyTable
from kokage_ui.htmx import InlineEdit

app = FastAPI()
ui = KokageUI(app)


# ── Data ──────────────────────────────────────────────


class User(BaseModel):
    id: str
    name: str
    email: str
    role: str


USERS: dict[str, User] = {
    "1": User(id="1", name="Alice", email="alice@example.com", role="admin"),
    "2": User(id="2", name="Bob", email="bob@example.com", role="editor"),
    "3": User(id="3", name="Charlie", email="charlie@example.com", role="viewer"),
}


# ── Helpers ───────────────────────────────────────────


def _inline(user: User, field: str) -> InlineEdit:
    return InlineEdit(
        getattr(user, field),
        edit_url=f"/users/{user.id}/edit/{field}",
        name=field,
    )


def _user_rows() -> list[list[object]]:
    return [
        [u.id, _inline(u, "name"), _inline(u, "email"), _inline(u, "role")]
        for u in USERS.values()
    ]


# ── Pages ─────────────────────────────────────────────


@ui.page("/")
def index():
    return Page(
        Div(
            H1("Inline Edit Demo", cls="text-2xl font-bold mb-4"),
            Card(
                DaisyTable(
                    headers=["ID", "Name", "Email", "Role"],
                    rows=_user_rows(),
                ),
                title="Users",
            ),
            cls="container mx-auto p-8",
        ),
        title="Inline Edit Demo",
    )


# ── Edit form endpoint ───────────────────────────────


@ui.fragment("/users/{user_id}/edit/{field}")
def edit_field(request: Request, user_id: str, field: str):
    user = USERS[user_id]
    return InlineEdit.form(
        value=getattr(user, field),
        name=field,
        save_url=f"/users/{user_id}",
        cancel_url=f"/users/{user_id}/view/{field}",
    )


# ── Save endpoint ────────────────────────────────────


@app.patch("/users/{user_id}")
async def update_user(user_id: str, request: Request):
    data = await request.form()
    field = str(data["_field"])
    value = str(data[field])
    user = USERS[user_id]
    setattr(user, field, value)
    component = InlineEdit(
        getattr(user, field),
        edit_url=f"/users/{user_id}/edit/{field}",
        name=field,
    )
    return HTMLResponse(component.render())


# ── Cancel endpoint ──────────────────────────────────


@ui.fragment("/users/{user_id}/view/{field}")
def view_field(request: Request, user_id: str, field: str):
    user = USERS[user_id]
    return InlineEdit(
        getattr(user, field),
        edit_url=f"/users/{user_id}/edit/{field}",
        name=field,
    )
