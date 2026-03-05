# Hello World

The simplest kokage-ui application.

## Full Code

```python
"""kokage-ui: Minimal hello world app."""

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
```

## Run

```bash
uv run uvicorn examples.hello:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

## Walkthrough

1. **Create a FastAPI app and wrap it with `KokageUI`**:

    ```python
    app = FastAPI()
    ui = KokageUI(app)
    ```

    `KokageUI(app)` mounts the bundled htmx.js and prepares the page/fragment decorators.

2. **Define a page route with `@ui.page("/")`**:

    ```python
    @ui.page("/")
    def home():
        ...
    ```

    This registers a `GET /` route that returns `HTMLResponse`.

3. **Return a `Page` with components**:

    ```python
    return Page(
        Card(
            H1("Hello, World!"),
            P("Built with FastAPI + htmx + DaisyUI. Pure Python."),
            actions=[DaisyButton("Get Started", color="primary")],
            title="Welcome to kokage-ui",
        ),
        title="Hello App",
    )
    ```

    - `Page(...)` generates a full HTML document with all CSS/JS dependencies
    - `Card(...)` creates a DaisyUI card with a title, body content, and action buttons
    - `H1`, `P` are standard HTML elements
    - `DaisyButton` renders a styled button with DaisyUI classes
