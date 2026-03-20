"""Template strings for kokage CLI scaffolding."""

# ---------- Common ----------

PYPROJECT_TEMPLATE = '''\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "kokage-ui",
]
'''

PYPROJECT_SQL_TEMPLATE = '''\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "kokage-ui[sql]",
]
'''

GITIGNORE_TEMPLATE = '''\
__pycache__/
*.py[cod]
.venv/
*.db
*.sqlite3
.env
dist/
*.egg-info/
'''

README_TEMPLATE = '''\
# {name}

Built with [kokage-ui](https://github.com/neka-nat/kokage-ui) — FastAPI + htmx + DaisyUI.

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn app:app --reload
```

Open http://localhost:8000 in your browser.
'''

# ---------- App Templates ----------

# Template registry: {key: (description, template_string, uses_sql)}
# Accessed by TEMPLATES dict at bottom of file.

APP_TEMPLATE = '''\
"""{name} — Built with kokage-ui."""

from fastapi import FastAPI
from kokage_ui import Card, DaisyButton, H1, KokageUI, P, Page

app = FastAPI()
ui = KokageUI(app)


@ui.page("/")
def home():
    return Page(
        Card(
            H1("Welcome to {name}!"),
            P("Built with FastAPI + htmx + DaisyUI."),
            actions=[DaisyButton("Get Started", color="primary")],
            title="{name}",
        ),
        title="{name}",
    )
'''

APP_CRUD_TEMPLATE = '''\
"""{name} — Built with kokage-ui."""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from kokage_ui import A, InMemoryStorage, KokageUI, Layout, NavBar

app = FastAPI()
ui = KokageUI(app)


class Item(BaseModel):
    id: str = ""
    name: str = Field(min_length=1, max_length=200)
    description: str = ""


storage = InMemoryStorage(Item)

layout = Layout(
    navbar=NavBar(
        start=A("{name}", cls="btn btn-ghost text-xl", href="/items"),
        end=A("New Item", cls="btn btn-primary btn-sm", href="/items/new"),
    ),
    title_suffix=" - {name}",
    include_toast=True,
)

ui.crud(
    "/items",
    model=Item,
    storage=storage,
    title="Items",
    layout=layout,
)
'''

APP_ADMIN_TEMPLATE = '''\
"""{name} — Admin dashboard built with kokage-ui."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel
from starlette.responses import RedirectResponse

from kokage_ui import AdminSite, ColumnFilter, SQLModelStorage, create_tables

engine = create_async_engine("sqlite+aiosqlite:///data.db")


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=100)
    email: str = ""
    role: str = "viewer"
    is_active: bool = True


class Article(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    author: str = ""
    status: str = "draft"


user_storage = SQLModelStorage(User, engine)
article_storage = SQLModelStorage(Article, engine)


async def seed_data():
    """Insert sample data if tables are empty."""
    _, total = await user_storage.list()
    if total == 0:
        await user_storage.create(User(name="Admin", email="admin@example.com", role="admin"))
        await user_storage.create(User(name="Editor", email="editor@example.com", role="editor"))
        await article_storage.create(Article(title="Getting Started", author="Admin", status="published"))
        await article_storage.create(Article(title="Draft Post", author="Editor", status="draft"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables(engine)
    await seed_data()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return RedirectResponse("/admin/")


admin = AdminSite(app, prefix="/admin", title="{name} Admin")

admin.register(
    User,
    storage=user_storage,
    icon="U",
    search_fields=["name", "email"],
    filters={{
        "role": ColumnFilter(
            type="select",
            options=[("admin", "Admin"), ("editor", "Editor"), ("viewer", "Viewer")],
        ),
    }},
)
admin.register(
    Article,
    storage=article_storage,
    icon="A",
    search_fields=["title", "author"],
    filters={{
        "status": ColumnFilter(
            type="select",
            options=[("draft", "Draft"), ("published", "Published")],
        ),
    }},
)
'''

APP_DASHBOARD_TEMPLATE = '''\
"""{name} — Dashboard built with kokage-ui."""

import random

from fastapi import FastAPI

from kokage_ui import (
    Card,
    Chart,
    ChartData,
    Dataset,
    Div,
    H1,
    KokageUI,
    Page,
    Stat,
    Stats,
)

app = FastAPI()
ui = KokageUI(app)


@ui.page("/")
def home():
    return Page(
        Div(
            H1("{name}", cls="text-3xl font-bold mb-6"),
            Stats(
                Stat(title="Revenue", value="${{:,.0f}}".format(random.randint(10000, 99999)), desc="+12% from last month"),
                Stat(title="Users", value="{{}},{{}}".format(random.randint(1, 9), random.randint(100, 999)), desc="+5% from last week"),
                Stat(title="Orders", value=str(random.randint(100, 999)), desc="Active this month"),
                cls="shadow mb-6",
            ),
            Div(
                Card(
                    Chart(
                        type="line",
                        data=ChartData(
                            labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                            datasets=[
                                Dataset(
                                    label="Revenue",
                                    data=[65, 59, 80, 81, 56, 72],
                                    borderColor="#36a2eb",
                                    fill=False,
                                ),
                            ],
                        ),
                        height="250px",
                    ),
                    title="Revenue Trend",
                ),
                Card(
                    Chart(
                        type="doughnut",
                        data=ChartData(
                            labels=["Electronics", "Books", "Clothing"],
                            datasets=[
                                Dataset(
                                    data=[45, 25, 30],
                                    backgroundColor=["#36a2eb", "#ff6384", "#ffce56"],
                                ),
                            ],
                        ),
                        height="250px",
                    ),
                    title="Sales by Category",
                ),
                cls="grid grid-cols-1 md:grid-cols-2 gap-6",
            ),
            cls="container mx-auto p-6",
        ),
        title="{name}",
        include_chartjs=True,
    )
'''

APP_CHAT_TEMPLATE = '''\
"""{name} — AI Chat built with kokage-ui."""

import asyncio

from fastapi import FastAPI

from kokage_ui import KokageUI

app = FastAPI()
ui = KokageUI(app)


@ui.chat("/", placeholder="Type a message...", send_label="Send", title="{name}")
async def chat(message: str):
    # Replace this with your LLM API call
    response = f"You said: **{{message}}**\\n\\nThis is a demo response. "
    response += "Integrate your preferred LLM (Claude, GPT, etc.) here."
    for char in response:
        yield char
        await asyncio.sleep(0.02)
'''

APP_AGENT_TEMPLATE = '''\
"""{name} — AI Agent built with kokage-ui."""

import asyncio
import json

from fastapi import FastAPI

from kokage_ui import KokageUI
from kokage_ui.ai import AgentEvent

app = FastAPI()
ui = KokageUI(app)


@ui.agent("/", placeholder="Ask the agent...", send_label="Send", title="{name}")
async def agent(message: str):
    yield AgentEvent(type="status", content="Thinking...")
    await asyncio.sleep(0.5)

    # Simulate a tool call
    yield AgentEvent(
        type="tool_call",
        call_id="tc1",
        tool_name="search",
        tool_input=json.dumps({{"query": message}}),
    )
    await asyncio.sleep(1.0)
    yield AgentEvent(
        type="tool_result",
        call_id="tc1",
        result=f"Found 3 results for '{{message}}'",
    )

    # Stream response text
    yield AgentEvent(type="status", content="Generating response...")
    response = f"Based on the search results for **{{message}}**, here is what I found.\\n\\n"
    response += "This is a demo agent. Replace the tool calls and LLM integration with your own logic."
    for char in response:
        yield AgentEvent(type="text", content=char)
        await asyncio.sleep(0.02)

    yield AgentEvent(
        type="done",
        metrics={{"tokens": 150, "duration_ms": 2500, "tool_calls": 1}},
    )
'''

# ---------- Add command templates ----------

PAGE_TEMPLATE = '''\
"""{name} page."""

from kokage_ui import Div, H1, KokageUI, Page


def register(ui: KokageUI) -> None:
    @ui.page("/{name}")
    def {name}_page():
        return Page(
            Div(
                H1("{title}", cls="text-3xl font-bold"),
                cls="container mx-auto p-6",
            ),
            title="{title}",
        )
'''

CRUD_MODEL_TEMPLATE = '''\
"""{model} model and storage."""

from pydantic import BaseModel, Field
from kokage_ui import InMemoryStorage


class {model}(BaseModel):
    id: str = ""
    name: str = Field(min_length=1, max_length=200)


{snake}_storage = InMemoryStorage({model})
'''

# ---------- Template registry ----------

TEMPLATES: dict[str, tuple[str, str, bool]] = {
    "basic": ("Minimal page with Card component", APP_TEMPLATE, False),
    "crud": ("CRUD app with model, storage, and layout", APP_CRUD_TEMPLATE, False),
    "admin": ("Admin dashboard with SQLite storage", APP_ADMIN_TEMPLATE, True),
    "dashboard": ("KPI stats and Chart.js charts", APP_DASHBOARD_TEMPLATE, False),
    "chat": ("AI chat interface with streaming", APP_CHAT_TEMPLATE, False),
    "agent": ("AI agent with tool execution panel", APP_AGENT_TEMPLATE, False),
}
