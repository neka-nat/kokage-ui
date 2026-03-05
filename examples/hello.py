"""kokage-ui: Minimal hello world app.

Run:
    uv run uvicorn examples.hello:app --reload

Open http://localhost:8000 in your browser.
"""

from fastapi import FastAPI

from kokage_ui import Card, DaisyButton, H1, KokageUI, P, Page

app = FastAPI()
ui = KokageUI(app)


@ui.page("/")
def home():
    return Page(
        Card(
            H1("Hello, World!"),
            P("Built with FastAPI + htmx + DaisyUI. Pure Python."),
            actions=[DaisyButton("Get Started", color="primary")],
            title="Welcome to kokage-ui",
        ),
        title="Hello App",
    )
