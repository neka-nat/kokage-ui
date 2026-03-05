# CRUD

kokage-ui can generate a full CRUD (Create, Read, Update, Delete) interface from a Pydantic model with a single method call.

## Quick Start

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from kokage_ui import KokageUI, InMemoryStorage

app = FastAPI()
ui = KokageUI(app)

class Todo(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=200)
    completed: bool = False

storage = InMemoryStorage(Todo)

ui.crud("/todos", model=Todo, storage=storage)
```

This registers the following routes:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/todos` | List page with search and pagination |
| GET | `/todos/_list` | Table fragment (htmx) |
| GET | `/todos/new` | Create form page |
| POST | `/todos/new` | Create handler |
| GET | `/todos/{id}` | Detail page |
| GET | `/todos/{id}/edit` | Edit form page |
| POST | `/todos/{id}/edit` | Update handler |
| DELETE | `/todos/{id}` | Delete handler |

## ui.crud() Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `prefix` | str | URL prefix (e.g., `"/todos"`) |
| `model` | type[BaseModel] | Pydantic model class |
| `storage` | Storage | Storage backend |
| `id_field` | str | Name of the ID field (default: `"id"`) |
| `per_page` | int | Items per page (default: 20) |
| `title` | str \| None | Display title (defaults to `ModelName + "s"`) |
| `exclude_fields` | list[str] \| None | Fields to exclude from all views |
| `table_exclude` | list[str] \| None | Fields to exclude from table view |
| `form_exclude` | list[str] \| None | Fields to exclude from forms |
| `page_wrapper` | Callable \| None | `callable(content, title) → Page` for custom layout |
| `layout` | Layout \| None | Layout instance (used as page_wrapper if page_wrapper not set) |
| `theme` | str | DaisyUI theme name (default: `"light"`) |

## Storage

`Storage` is an abstract base class that defines the interface for data persistence.

```python
from kokage_ui import Storage

class Storage(ABC, Generic[T]):
    async def list(self, *, skip=0, limit=20, search=None) -> tuple[list[T], int]: ...
    async def get(self, id: str) -> T | None: ...
    async def create(self, data: T) -> T: ...
    async def update(self, id: str, data: T) -> T | None: ...
    async def delete(self, id: str) -> bool: ...
```

All methods are `async`. The `list` method returns a tuple of `(items, total_count)` for pagination.

### InMemoryStorage

A built-in dict-based storage implementation with auto-generated UUIDs:

```python
from kokage_ui import InMemoryStorage

storage = InMemoryStorage(Todo)

# With initial data
storage = InMemoryStorage(Todo, initial=[
    Todo(id="1", title="First"),
    Todo(id="2", title="Second"),
])
```

`InMemoryStorage` supports full-text search across all fields via the `search` parameter in `list()`.

### Custom Storage

Implement the `Storage` ABC to connect to any database:

```python
from kokage_ui import Storage

class PostgresStorage(Storage[User]):
    def __init__(self, pool):
        self.pool = pool

    async def list(self, *, skip=0, limit=20, search=None):
        # Your SQL queries here
        ...

    async def get(self, id: str):
        ...

    async def create(self, data):
        ...

    async def update(self, id: str, data):
        ...

    async def delete(self, id: str):
        ...
```

## Using Layout with CRUD

Wrap CRUD pages in a consistent layout:

```python
from kokage_ui import Layout, NavBar, A

layout = Layout(
    navbar=NavBar(
        start=A("My App", cls="btn btn-ghost text-xl", href="/"),
        end=A("New Todo", cls="btn btn-primary btn-sm", href="/todos/new"),
    ),
    title_suffix=" - My App",
    include_toast=True,
)

ui.crud("/todos", model=Todo, storage=storage, layout=layout)
```

Or use a custom `page_wrapper` function:

```python
from kokage_ui import Page

def my_wrapper(content, title):
    return Page(
        NavBar(start=A("App", href="/")),
        content,
        title=f"{title} - App",
    )

ui.crud("/todos", model=Todo, storage=storage, page_wrapper=my_wrapper)
```

## Pagination

The `Pagination` component is used internally by CRUD but can also be used standalone:

```python
from kokage_ui import Pagination

Pagination(
    current_page=2,
    total_pages=10,
    base_url="/items/_list",
    target="#table-container",
    search="query",
)
```

## Features

- **Search** — Built-in `SearchFilter` with debounce on the list page
- **Pagination** — htmx-powered page navigation
- **Validation** — Pydantic validation errors shown inline on forms
- **Toast notifications** — Success/error messages after create, update, delete
- **Confirm delete** — JavaScript confirmation dialog before deletion
- **htmx integration** — Form submissions and table updates use htmx for smooth UX
