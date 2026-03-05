"""Template strings for kokage CLI scaffolding."""

PYPROJECT_TEMPLATE = '''\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "kokage-ui",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
'''

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
