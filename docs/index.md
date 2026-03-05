# kokage-ui

**Add htmx + DaisyUI based UI to FastAPI with pure Python.**

kokage-ui lets you build interactive web UIs entirely in Python — no templates, no JavaScript, no build step. Define your pages as Python functions, compose HTML with class-based components, and get DaisyUI styling and htmx interactivity for free.

## Quick Example

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
            P("Built with FastAPI + htmx + DaisyUI."),
            actions=[DaisyButton("Click me", color="primary")],
            title="Welcome",
        ),
        title="My App",
    )
```

## Features

| Feature | Description |
|---------|-------------|
| **Pure Python** | No HTML templates or JavaScript needed |
| **50+ HTML Elements** | Full set of typed HTML element classes |
| **DaisyUI Components** | Card, NavBar, Alert, Badge, Hero, Stats, Toast, and more |
| **Pydantic Integration** | Auto-generate forms, tables, and detail views from `BaseModel` |
| **One-line CRUD** | Full CRUD UI from a single `ui.crud()` call |
| **htmx Built-in** | AutoRefresh, SearchFilter, InfiniteScroll, SSE, and more |
| **XSS Protection** | All output escaped via `markupsafe` by default |

## Architecture

```
┌──────────────────────────────────────────────┐
│  FastAPI Application                         │
│  ┌────────────────────────────────────────┐  │
│  │  KokageUI(app)                        │  │
│  │  ├── @ui.page("/")     → full pages   │  │
│  │  ├── @ui.fragment("/") → htmx partials│  │
│  │  └── ui.crud("/items") → full CRUD    │  │
│  └────────────────────────────────────────┘  │
│                    ▼                         │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │ elements │ │ components│ │   models    │  │
│  │ Div, H1  │ │ Card,Hero │ │ ModelForm   │  │
│  │ Form,... │ │ NavBar,...│ │ ModelTable  │  │
│  └──────────┘ └───────────┘ └────────────┘  │
│                    ▼                         │
│  ┌──────────────────────────────────────┐    │
│  │  htmx (local) + DaisyUI/TW (CDN)    │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

## Next Steps

- [Getting Started](getting-started.md) — Install and build your first app
- [HTML Elements](guide/elements.md) — Learn the component system
- [DaisyUI Components](guide/components.md) — High-level UI components
- [Examples](examples/hello.md) — See complete working apps
