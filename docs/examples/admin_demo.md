# Admin Demo

A complete admin dashboard with authentication, multi-model management, and theme switching.

## Run

```bash
uvicorn examples.admin_demo:app --reload
```

Open [http://localhost:8000](http://localhost:8000) and login with `admin` / `admin`.

## Code

```python
--8<-- "examples/admin_demo.py"
```

## Features Demonstrated

- **AdminSite** — Auto-generated admin panel with sidebar, DataGrid, CRUD forms
- **LoginForm** — Pre-built login form with error display
- **@protected** — Route protection with cookie-based auth
- **UserMenu** — Dropdown user menu in navbar
- **ThemeSwitcher / DarkModeToggle** — Runtime theme switching
- **InMemoryStorage** — Three models (User, Product, Order) managed simultaneously

## Key Patterns

### Authentication Flow

1. `get_current_user()` reads `username` cookie
2. `AdminSite(auth_check=get_current_user)` protects all admin routes
3. Unauthenticated users are redirected to `/login`
4. After login, cookie is set and user can access `/admin/`

### Multiple Model Registration

```python
admin.register(User, storage=user_storage, icon="U", search_fields=["name", "email"])
admin.register(Product, storage=product_storage, icon="P", search_fields=["name", "category"])
admin.register(Order, storage=order_storage, icon="O", list_fields=["product", "quantity", "status"])
```

Each `register()` call adds the model to the sidebar and creates all CRUD routes.
