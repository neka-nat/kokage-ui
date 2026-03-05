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
| **25+ DaisyUI Components** | Card, NavBar, Modal, Tabs, Accordion, Hero, Stats, Toast, and more |
| **Pydantic Integration** | Auto-generate forms, tables, and detail views from `BaseModel` |
| **One-line CRUD** | Full CRUD UI from a single `ui.crud()` call |
| **DataGrid** | Sortable, filterable tables with pagination, bulk actions, CSV export |
| **Admin Dashboard** | Django-like admin panel auto-generated from models |
| **Auth UI** | Login, register, user menu, role guard, route protection |
| **Theme System** | Dark mode toggle and full theme switcher with persistence |
| **Real-time Notifications** | SSE-based push notifications as toast alerts |
| **SQL Storage** | Async database persistence with SQLModel |
| **htmx Built-in** | AutoRefresh, SearchFilter, InfiniteScroll, SSE, and more |
| **Charts & Markdown** | Chart.js charts, syntax-highlighted code blocks, Markdown rendering |
| **CLI Scaffolding** | Generate projects and pages from the command line |
| **XSS Protection** | All output escaped via `markupsafe` by default |

## Architecture

```
┌──────────────────────────────────────────────────┐
│  FastAPI Application                             │
│  ┌────────────────────────────────────────────┐  │
│  │  KokageUI(app)                            │  │
│  │  ├── @ui.page("/")     → full pages       │  │
│  │  ├── @ui.fragment("/") → htmx partials    │  │
│  │  └── ui.crud("/items") → full CRUD        │  │
│  └────────────────────────────────────────────┘  │
│                      ▼                           │
│  ┌──────────┐ ┌───────────┐ ┌──────────────┐    │
│  │ elements │ │ components│ │    models     │    │
│  │ Div, H1  │ │ Card,Hero │ │ ModelForm     │    │
│  │ Form,... │ │ NavBar,...│ │ ModelTable    │    │
│  └──────────┘ └───────────┘ └──────────────┘    │
│  ┌──────────┐ ┌───────────┐ ┌──────────────┐    │
│  │ datagrid │ │   auth    │ │    admin      │    │
│  │ DataGrid │ │ LoginForm │ │ AdminSite     │    │
│  │ filters  │ │ protected │ │ ModelAdmin    │    │
│  └──────────┘ └───────────┘ └──────────────┘    │
│                      ▼                           │
│  ┌──────────────────────────────────────────┐    │
│  │  htmx (local) + DaisyUI/TW (CDN)        │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

## Next Steps

- [Getting Started](getting-started.md) — Install and build your first app
- [HTML Elements](guide/elements.md) — Learn the component system
- [DaisyUI Components](guide/components.md) — High-level UI components
- [CRUD](guide/crud.md) — One-line CRUD generation
- [DataGrid](guide/datagrid.md) — Advanced sortable/filterable tables
- [Admin Dashboard](guide/admin.md) — Auto-generated admin panel
- [Auth](guide/auth.md) — Authentication and authorization UI
- [Theme](guide/theme.md) — Theme switching
- [Notifications](guide/notifications.md) — Real-time push notifications
- [Examples](examples/hello.md) — See complete working apps
