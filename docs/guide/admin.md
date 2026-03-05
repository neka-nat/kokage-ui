# Admin Dashboard

kokage-ui can auto-generate a Django-like admin panel from your Pydantic models. Register models with `AdminSite` and get a full management interface with sidebar navigation, DataGrid list views, create/edit forms, detail views, bulk actions, and CSV export.

## Quick Start

```python
from fastapi import FastAPI
from kokage_ui import KokageUI, AdminSite, InMemoryStorage
from pydantic import BaseModel, Field

app = FastAPI()
ui = KokageUI(app)

class User(BaseModel):
    id: str = ""
    name: str = Field(min_length=1)
    email: str = ""
    is_active: bool = True

class Product(BaseModel):
    id: str = ""
    name: str = Field(min_length=1)
    price: float = Field(ge=0)

admin = AdminSite(app, prefix="/admin", title="My Admin")
admin.register(User, storage=InMemoryStorage(User))
admin.register(Product, storage=InMemoryStorage(Product))
```

This generates:

- **Dashboard** at `/admin/` — overview with model cards and item counts
- **List pages** at `/admin/user/`, `/admin/product/` — DataGrid with sort, filter, pagination
- **Create/Edit/Detail/Delete** pages for each model
- **Bulk delete** and **CSV export** endpoints
- **Sidebar navigation** with all registered models

## AdminSite Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | FastAPI | FastAPI application instance |
| `prefix` | str | URL prefix (default: `"/admin"`) |
| `title` | str | Site title in navbar (default: `"Admin"`) |
| `auth_check` | Callable \| None | `(Request) -> user \| None` for authentication |
| `theme` | str | DaisyUI theme (default: `"corporate"`) |
| `logout_url` | str | Logout URL for UserMenu (default: `"/logout"`) |

## register() Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | type[BaseModel] | Pydantic model class |
| `storage` | Storage | Storage backend |
| `name` | str | URL slug (default: auto from model name) |
| `title` | str | Display name (default: `ModelName + "s"`) |
| `icon` | str | Sidebar icon (default: first letter) |
| `list_fields` | list[str] \| None | Fields to show in list view |
| `search_fields` | list[str] \| None | Searchable fields |
| `form_exclude` | list[str] \| None | Fields to exclude from forms |
| `list_exclude` | list[str] \| None | Fields to exclude from list |
| `per_page` | int | Items per page (default: 20) |
| `id_field` | str | Primary key field (default: `"id"`) |

## Authentication

Protect the admin panel by providing an `auth_check` function:

```python
async def get_user(request: Request):
    token = request.cookies.get("auth_token")
    if not token:
        return None
    return {"username": "admin", "role": "admin"}

admin = AdminSite(app, auth_check=get_user)
```

When `auth_check` returns `None`, all admin routes redirect to `/login`.

## With SQLModel Storage

```python
from sqlalchemy.ext.asyncio import create_async_engine
from kokage_ui import SQLModelStorage, create_tables

engine = create_async_engine("sqlite+aiosqlite:///admin.db")

@app.on_event("startup")
async def startup():
    await create_tables(engine)

admin = AdminSite(app)
admin.register(User, storage=SQLModelStorage(User, engine))
```

## Generated Routes

For each registered model (e.g., `User` with prefix `/admin`):

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/` | Dashboard with model cards |
| GET | `/admin/user/` | List page (DataGrid) |
| GET | `/admin/user/_list` | List fragment (htmx) |
| POST | `/admin/user/_bulk_delete` | Bulk delete |
| GET | `/admin/user/_csv` | CSV export |
| GET | `/admin/user/new` | Create form |
| POST | `/admin/user/new` | Create handler |
| GET | `/admin/user/{id}` | Detail page |
| GET | `/admin/user/{id}/edit` | Edit form |
| POST | `/admin/user/{id}/edit` | Edit handler |
| DELETE | `/admin/user/{id}` | Delete handler |
