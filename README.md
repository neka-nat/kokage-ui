![logo](assets/logo.svg)

[![PyPI version](https://img.shields.io/pypi/v/kokage-ui)](https://pypi.org/project/kokage-ui/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Add beautiful UI to FastAPI with pure Python. No JavaScript, no templates, no frontend build step.**

## Quick Start

```bash
pip install kokage-ui
```

```python
from fastapi import FastAPI
from kokage_ui import KokageUI, Page, Card, H1, P, DaisyButton

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

```bash
uvicorn hello:app --reload
```

## Features

- **50+ HTML Elements** — `Div`, `H1`, `Form`, `Input`, etc. as Python classes
- **DaisyUI Components** — `Card`, `Hero`, `NavBar`, `Alert`, `Badge`, `Stats`, `Toast`, `Layout`
- **Pydantic → UI** — Auto-generate forms, tables, detail views from `BaseModel`
- **One-line CRUD** — `ui.crud("/users", model=User, storage=storage)`
- **htmx Patterns** — `AutoRefresh`, `SearchFilter`, `InfiniteScroll`, `SSEStream`, `ConfirmDelete`
- **XSS Protection** — Output escaped via `markupsafe` by default

## Examples

| Example | Description | Run |
|---|---|---|
| [hello.py](examples/hello.py) | Minimal app | `uvicorn examples.hello:app` |
| [todo.py](examples/todo.py) | CRUD todo app | `uvicorn examples.todo:app` |
| [dashboard.py](examples/dashboard.py) | Full dashboard | `uvicorn examples.dashboard:app` |

## Documentation

For detailed guides, component reference, and API docs, see the [full documentation](https://neka-nat.github.io/kokage-ui/).

## License

MIT
