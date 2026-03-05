# Authentication & Authorization

kokage-ui provides pre-built authentication UI components and route protection decorators.

## LoginForm

```python
from kokage_ui import LoginForm, Page

@ui.page("/login")
def login_page():
    return Page(
        LoginForm(
            action="/login",
            register_url="/register",
            forgot_url="/forgot-password",
        ),
        title="Login",
    )
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | str | Form submit URL (default: `"/login"`) |
| `method` | str | HTTP method (default: `"post"`) |
| `title` | str | Form title (default: `"Login"`) |
| `username_label` | str | Username field label (default: `"Username"`) |
| `username_field` | str | Username input name (default: `"username"`) |
| `password_label` | str | Password field label (default: `"Password"`) |
| `password_field` | str | Password input name (default: `"password"`) |
| `submit_text` | str | Submit button text (default: `"Login"`) |
| `submit_color` | str | Button color (default: `"primary"`) |
| `register_url` | str \| None | Registration page URL |
| `forgot_url` | str \| None | Forgot password page URL |
| `error` | str \| None | Error message to display |
| `use_email` | bool | Use email input type (default: `False`) |

## RegisterForm

```python
from kokage_ui import RegisterForm

RegisterForm(
    action="/register",
    login_url="/login",
    confirm_password=True,
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | str | Form submit URL (default: `"/register"`) |
| `title` | str | Form title (default: `"Create Account"`) |
| `fields` | list[tuple] \| None | Custom fields: `[(name, label, type), ...]` |
| `confirm_password` | bool | Add password confirmation field (default: `True`) |
| `login_url` | str \| None | Login page link URL |
| `error` | str \| None | Error message to display |

## UserMenu

Dropdown menu for the navigation bar:

```python
from kokage_ui import NavBar, UserMenu

NavBar(
    start=A("My App", href="/"),
    end=UserMenu(
        username="alice@example.com",
        avatar_url="https://example.com/avatar.jpg",
        menu_items=[("Settings", "/settings"), ("Help", "/help")],
        logout_url="/logout",
    ),
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `username` | str | Display name (required) |
| `avatar_url` | str \| None | Avatar image URL |
| `logout_url` | str | Logout URL (default: `"/logout"`) |
| `menu_items` | list[tuple] \| None | `[(label, href), ...]` for dropdown items |

## RoleGuard

Conditionally render content based on user role (server-side, no HTML leak):

```python
from kokage_ui import RoleGuard

RoleGuard(
    A("Admin Panel", href="/admin"),
    role="admin",
    user_role=current_user.role,
    fallback=Span("Access denied"),
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Content to show if authorized |
| `role` | str \| list[str] | Required role(s) |
| `user_role` | str \| list[str] \| None | Current user's role(s) |
| `fallback` | Any | Content when unauthorized (default: empty) |

## @protected Decorator

Protect page/fragment routes with authentication and optional role checking:

```python
from kokage_ui import protected

async def get_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None
    return {"username": "alice", "role": "admin"}

@ui.page("/dashboard")
@protected(get_user, role="admin", redirect_to="/login")
async def dashboard(request: Request):
    user = request.state.user
    return Page(H1(f"Welcome, {user['username']}"))
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `auth_check` | Callable | `(Request) -> user \| None` (sync or async) |
| `redirect_to` | str | Redirect URL when unauthenticated (default: `"/login"`) |
| `role` | str \| list[str] \| None | Required role(s) for authorization |
| `role_key` | str | Key/attribute name for user role (default: `"role"`) |

When `auth_check` returns `None`, the user is redirected. When a role is required but not matched, a 403 Forbidden is raised. The authenticated user is set on `request.state.user`.
