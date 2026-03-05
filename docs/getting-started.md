# Getting Started

## Installation

=== "pip"

    ```bash
    pip install kokage-ui
    ```

=== "uv"

    ```bash
    uv add kokage-ui
    ```

kokage-ui requires Python 3.11+ and installs FastAPI automatically.

## Your First App

Create a file called `app.py`:

```python
from fastapi import FastAPI
from kokage_ui import KokageUI, Page, Card, H1, P, DaisyButton

app = FastAPI()
ui = KokageUI(app)

@ui.page("/")
def home():
    return Page(
        Card(
            H1("Hello, kokage!"),
            P("Your first kokage-ui application."),
            actions=[DaisyButton("Get Started", color="primary")],
            title="Welcome",
        ),
        title="My First App",
    )
```

## Run It

=== "uvicorn"

    ```bash
    uvicorn app:app --reload
    ```

=== "fastapi CLI"

    ```bash
    fastapi dev app.py
    ```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## How It Works

1. **`KokageUI(app)`** — Wraps your FastAPI app. Mounts the bundled htmx.js and sets up static file serving.

2. **`@ui.page("/")`** — Registers a route that returns a full HTML page. The decorated function should return a `Page`, `Component`, or `str`.

3. **`Page(...)`** — Generates a complete `<!DOCTYPE html>` document with htmx and DaisyUI/Tailwind CSS automatically loaded via CDN.

4. **`Card(...)`, `H1(...)`, etc.** — Python classes that render to HTML. Children are positional args, attributes are keyword args.

## Adding Interactivity

Use `@ui.fragment()` for htmx partial responses:

```python
from kokage_ui import Div, DaisyButton

@ui.page("/")
def home():
    return Page(
        Div(
            DaisyButton("Load Data", color="primary",
                        hx_get="/api/data", hx_target="#result"),
            Div(id="result"),
        ),
        title="Interactive App",
    )

@ui.fragment("/api/data")
def load_data():
    return Div("Data loaded via htmx!")
```

Clicking the button sends an htmx GET request to `/api/data` and inserts the response into `#result`.

## Adding CRUD

Generate a full CRUD interface from a Pydantic model in one line:

```python
from pydantic import BaseModel, Field
from kokage_ui import InMemoryStorage

class Todo(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=200)
    completed: bool = False

storage = InMemoryStorage(Todo)

ui.crud("/todos", model=Todo, storage=storage)
```

This creates list, create, detail, edit, and delete pages at `/todos`.

## Next Steps

- [HTML Elements](guide/elements.md) — Full component reference
- [DaisyUI Components](guide/components.md) — Cards, alerts, navbars, and more
- [Pages & Layout](guide/pages.md) — Page structure and layouts
- [CRUD](guide/crud.md) — One-line CRUD generation
