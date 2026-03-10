"""Rich text editor demo with Quill.

Run:
    uv run uvicorn examples.richtext_demo:app --reload

Open http://localhost:8000/articles in your browser.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field

from kokage_ui import A, InMemoryStorage, KokageUI, Layout, NavBar, RichTextField

app = FastAPI()
ui = KokageUI(app)


@app.get("/")
def root():
    from starlette.responses import RedirectResponse

    return RedirectResponse("/articles")


class Article(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=200)
    body: Annotated[str, RichTextField(placeholder="Write your article...")] = ""


INITIAL_ARTICLES = [
    Article(id="1", title="Hello World", body="<p>Welcome to the <strong>rich text</strong> demo!</p>"),
]

storage = InMemoryStorage(Article, initial=INITIAL_ARTICLES)

layout = Layout(
    navbar=NavBar(
        start=A("Rich Text Demo", cls="btn btn-ghost text-xl", href="/articles"),
        end=A("New Article", cls="btn btn-primary btn-sm", href="/articles/new"),
    ),
    title_suffix=" - Rich Text Demo",
    include_toast=True,
    include_quill=True,
)

ui.crud(
    "/articles",
    model=Article,
    storage=storage,
    title="Articles",
    layout=layout,
)
