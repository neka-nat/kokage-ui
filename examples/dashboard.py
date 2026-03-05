"""kokage-ui sample: Dashboard application.

Run:
    uv run uvicorn examples.dashboard:app --reload

Open http://localhost:8000 in your browser.
"""

import enum
import random
from typing import Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from kokage_ui import (
    A,
    Alert,
    AutoRefresh,
    Card,
    DaisyButton,
    DaisyTable,
    Div,
    Form,
    H1,
    H2,
    Hero,
    InMemoryStorage,
    KokageUI,
    ModelDetail,
    ModelForm,
    ModelTable,
    NavBar,
    P,
    Page,
    SearchFilter,
    Span,
    Stat,
    Stats,
)

app = FastAPI()
ui = KokageUI(app)


# --- Pydantic models for the demo ---


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


# Sample data
INITIAL_USERS = [
    User(id="1", name="Tanaka Taro", email="tanaka@example.com", age=35, role=Role.ADMIN, is_active=True, bio="System administrator"),
    User(id="2", name="Suzuki Hanako", email="suzuki@example.com", age=28, role=Role.EDITOR, is_active=True),
    User(id="3", name="Sato Jiro", email="sato@example.com", age=42, role=Role.VIEWER, is_active=False),
    User(id="4", name="Takahashi Misaki", email="takahashi@example.com", age=31, role=Role.EDITOR, is_active=True),
    User(id="5", name="Ito Kenichi", email="ito@example.com", age=50, role=Role.ADMIN, is_active=True),
    User(id="6", name="Yamamoto Yuki", email="yamamoto@example.com", age=24, role=Role.VIEWER, is_active=True),
    User(id="7", name="Nakamura Risa", email="nakamura@example.com", age=33, role=Role.EDITOR, is_active=True),
    User(id="8", name="Kobayashi Sota", email="kobayashi@example.com", age=45, role=Role.ADMIN, is_active=False),
]

# Sample data for search demo (dict-based)
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
    """Wrap CRUD content with the navbar."""
    return Page(
        _navbar(),
        content,
        title=f"{title} - kokage Dashboard",
        theme="light",
    )


# Register CRUD routes for User model
ui.crud(
    "/users",
    model=User,
    storage=storage,
    title="Users",
    form_exclude=["bio"],
    page_wrapper=_page_wrapper,
)


@ui.page("/")
def index():
    return Page(
        _navbar(),
        Div(
            Hero(
                H1("kokage-ui Demo", cls="text-5xl font-bold"),
                P(
                    "FastAPI + htmx + DaisyUI",
                    cls="py-4 text-lg",
                ),
                DaisyButton("Get Started", color="primary", size="lg"),
                min_height="50vh",
            ),
            H2("Live Stats (auto-refresh every 3s)", cls="text-2xl font-bold mt-8 mb-4 px-4"),
            AutoRefresh(
                Span("Loading...", cls="loading loading-spinner"),
                url="/api/stats",
                interval=3,
            ),
            H2("User Search", cls="text-2xl font-bold mt-8 mb-4 px-4"),
            Div(
                SearchFilter(
                    url="/api/users/search",
                    target="#user-table",
                    placeholder="Search users...",
                ),
                cls="px-4 mb-4",
            ),
            Div(id="user-table"),
            cls="container mx-auto",
        ),
        title="kokage Dashboard",
        theme="light",
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
    filtered = [u for u in USERS_DICT if q.lower() in u["name"].lower()] if q else USERS_DICT
    return DaisyTable(
        headers=["Name", "Email", "Role"],
        rows=[[u["name"], u["email"], u["role"]] for u in filtered],
        zebra=True,
    )
