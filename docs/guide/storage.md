# SQL Storage

kokage-ui provides `SQLModelStorage` for async database persistence using SQLModel and SQLAlchemy.

## Installation

```bash
pip install kokage-ui[sql]
```

## Quick Start

```python
from sqlmodel import SQLModel, Field
from sqlalchemy.ext.asyncio import create_async_engine
from kokage_ui import KokageUI, SQLModelStorage, create_tables

# Define a SQLModel (works as both Pydantic BaseModel and SQLAlchemy ORM model)
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1)
    email: str = ""
    is_active: bool = True

# Create async engine
engine = create_async_engine("sqlite+aiosqlite:///app.db")

app = FastAPI()
ui = KokageUI(app)

@app.on_event("startup")
async def startup():
    await create_tables(engine)

# Use with CRUD
storage = SQLModelStorage(User, engine)
ui.crud("/users", model=User, storage=storage, title="Users")
```

## SQLModelStorage

```python
SQLModelStorage(model, engine, *, id_field="id")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | type[SQLModel] | SQLModel class with `table=True` |
| `engine` | AsyncEngine | SQLAlchemy async engine |
| `id_field` | str | Primary key field name (default: `"id"`) |

### Methods

All methods from the `Storage` ABC are implemented:

| Method | Description |
|--------|-------------|
| `list(skip, limit, search)` | Query with pagination and full-text search across string fields |
| `get(id)` | Fetch by primary key |
| `create(data)` | Insert new record (auto-increment IDs handled) |
| `update(id, data)` | Update existing record |
| `delete(id)` | Delete by primary key |

### Search

The `search` parameter in `list()` automatically searches across all string fields using SQL `LIKE '%query%'` with `OR` conditions.

## create_tables

```python
await create_tables(engine)
```

Creates all SQLModel tables. Safe to call multiple times (idempotent).

## Database Backends

SQLModelStorage works with any SQLAlchemy async-compatible database:

```python
# SQLite (development)
engine = create_async_engine("sqlite+aiosqlite:///app.db")

# PostgreSQL
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

# MySQL
engine = create_async_engine("mysql+aiomysql://user:pass@localhost/db")
```

## With AdminSite

```python
from kokage_ui import AdminSite

admin = AdminSite(app, title="My Admin")
admin.register(User, storage=SQLModelStorage(User, engine))
admin.register(Product, storage=SQLModelStorage(Product, engine))
```
