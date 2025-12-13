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
    name: str = Field(min_length=1, max_length=100)
    email: str
    age: int = Field(ge=0, le=150, default=30)
    role: Role = Role.VIEWER
    is_active: bool = True
    bio: str = Field(default="", max_length=500)


# Sample data (dict for search, Pydantic instances for ModelTable/ModelDetail)
USERS_DICT = [
    {"name": "Tanaka Taro", "email": "tanaka@example.com", "role": "Admin"},
    {"name": "Suzuki Hanako", "email": "suzuki@example.com", "role": "Editor"},
    {"name": "Sato Jiro", "email": "sato@example.com", "role": "Viewer"},
    {"name": "Takahashi Misaki", "email": "takahashi@example.com", "role": "Editor"},
    {"name": "Ito Kenichi", "email": "ito@example.com", "role": "Admin"},
    {"name": "Yamamoto Yuki", "email": "yamamoto@example.com", "role": "Viewer"},
    {"name": "Nakamura Risa", "email": "nakamura@example.com", "role": "Editor"},
    {"name": "Kobayashi Sota", "email": "kobayashi@example.com", "role": "Admin"},
]

USERS = [
    User(name="Tanaka Taro", email="tanaka@example.com", age=35, role=Role.ADMIN, is_active=True, bio="System administrator"),
    User(name="Suzuki Hanako", email="suzuki@example.com", age=28, role=Role.EDITOR, is_active=True),
    User(name="Sato Jiro", email="sato@example.com", age=42, role=Role.VIEWER, is_active=False),
    User(name="Takahashi Misaki", email="takahashi@example.com", age=31, role=Role.EDITOR, is_active=True),
    User(name="Ito Kenichi", email="ito@example.com", age=50, role=Role.ADMIN, is_active=True),
    User(name="Yamamoto Yuki", email="yamamoto@example.com", age=24, role=Role.VIEWER, is_active=True),
    User(name="Nakamura Risa", email="nakamura@example.com", age=33, role=Role.EDITOR, is_active=True),
    User(name="Kobayashi Sota", email="kobayashi@example.com", age=45, role=Role.ADMIN, is_active=False),
]


def _navbar():
    return NavBar(
        start=A("kokage Dashboard", cls="btn btn-ghost text-xl", href="/"),
        end=Div(
            A("Home", cls="btn btn-ghost", href="/"),
            A("Users", cls="btn btn-ghost", href="/users"),
            A("New User", cls="btn btn-ghost", href="/users/new"),
        ),
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


@ui.page("/users")
def users_page():
    return Page(
        _navbar(),
        Div(
            H1("User Management", cls="text-3xl font-bold mb-6"),
            Alert("This is a demo page with ModelTable auto-generation.", variant="info"),
            Div(
                ModelTable(
                    User,
                    rows=USERS,
                    exclude=["bio", "password"],
                    zebra=True,
                ),
                cls="mt-4",
            ),
            cls="container mx-auto p-4",
        ),
        title="Users - kokage Dashboard",
    )


@ui.page("/users/new")
def new_user_page():
    return Page(
        _navbar(),
        Div(
            H1("New User", cls="text-3xl font-bold mb-6"),
            Alert("This form is auto-generated from a Pydantic model.", variant="info"),
            Div(
                ModelForm(
                    User,
                    action="/users/new",
                    method="post",
                    submit_text="Create User",
                    submit_color="primary",
                ),
                cls="mt-4 max-w-lg",
            ),
            cls="container mx-auto p-4",
        ),
        title="New User - kokage Dashboard",
    )


@ui.page("/users/{idx}")
def user_detail_page(idx: int):
    if idx < 0 or idx >= len(USERS):
        return Page(
            _navbar(),
            Div(
                Alert("User not found.", variant="error"),
                cls="container mx-auto p-4",
            ),
            title="Not Found - kokage Dashboard",
        )
    user = USERS[idx]
    return Page(
        _navbar(),
        Div(
            H1("User Detail", cls="text-3xl font-bold mb-6"),
            Alert("This detail view is auto-generated from a Pydantic model instance.", variant="info"),
            Div(
                ModelDetail(user, title=user.name),
                cls="mt-4 max-w-lg",
            ),
            cls="container mx-auto p-4",
        ),
        title=f"{user.name} - kokage Dashboard",
    )
