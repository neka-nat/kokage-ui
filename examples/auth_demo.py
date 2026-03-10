"""kokage-ui: Authentication + Admin demo.

Run:
    uv run uvicorn examples.auth_demo:app --reload

Open http://localhost:8000 in your browser.

Features demonstrated:
    - LoginForm / RegisterForm components
    - Cookie-based authentication
    - protected decorator for page-level auth
    - UserMenu in navigation
    - RoleGuard for role-based rendering
    - AdminSite with auth_check
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from kokage_ui import (
    A,
    AdminSite,
    Card,
    ColumnFilter,
    Div,
    H1,
    InMemoryStorage,
    KokageUI,
    LoginForm,
    Nav,
    Page,
    RegisterForm,
    RoleGuard,
    UserMenu,
    protected,
)

app = FastAPI()
ui = KokageUI(app)

# ---------- Models ----------


class User(BaseModel):
    id: str = ""
    name: str = Field(min_length=1, max_length=100)
    email: str = ""
    role: str = "viewer"
    is_active: bool = True


class Article(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=200)
    author: str = ""
    status: str = "draft"


# ---------- Storage ----------

user_storage = InMemoryStorage(
    User,
    initial=[
        User(id="1", name="Admin User", email="admin@example.com", role="admin"),
        User(id="2", name="Editor", email="editor@example.com", role="editor"),
        User(id="3", name="Viewer", email="viewer@example.com", role="viewer"),
    ],
)

article_storage = InMemoryStorage(
    Article,
    initial=[
        Article(id="1", title="Getting Started", author="Admin User", status="published"),
        Article(id="2", title="Draft Post", author="Editor", status="draft"),
    ],
)

# Simple in-memory session store: {token: user_dict}
_sessions: dict[str, dict] = {}


# ---------- Auth Helpers ----------


async def get_current_user(request: Request) -> dict | None:
    """Extract user from cookie-based session."""
    token = request.cookies.get("session")
    if not token:
        return None
    return _sessions.get(token)


# ---------- Pages ----------


@ui.page("/")
def index():
    return Page(
        Div(
            Card(
                H1("Auth Demo"),
                Div(
                    A("Login", cls="btn btn-primary mr-2", href="/login"),
                    A("Register", cls="btn btn-outline", href="/register"),
                    cls="flex gap-2",
                ),
                title="kokage-ui Authentication Demo",
            ),
            cls="flex items-center justify-center min-h-screen",
        ),
        title="Auth Demo",
    )


@ui.page("/login")
def login_page(request: Request):
    error = request.query_params.get("error")
    return Page(
        LoginForm(
            action="/login",
            register_url="/register",
            error=error,
        ),
        title="Login",
    )


@ui.page("/register")
def register_page(request: Request):
    error = request.query_params.get("error")
    return Page(
        RegisterForm(
            action="/register",
            login_url="/login",
            error=error,
        ),
        title="Register",
    )


@app.post("/login")
async def do_login(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    if not username or not password:
        return RedirectResponse("/login?error=Please+fill+all+fields", status_code=302)

    # Demo: accept any username/password, look up user by name
    items = await user_storage.list()
    user_data = None
    for u in items:
        if u.name.lower() == str(username).lower() or u.email.lower() == str(username).lower():
            user_data = {"username": u.name, "role": u.role}
            break

    if user_data is None:
        # For demo: create a session for any username
        user_data = {"username": str(username), "role": "viewer"}

    import secrets

    token = secrets.token_hex(16)
    _sessions[token] = user_data

    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("session", token, httponly=True)
    return response


@app.post("/register")
async def do_register(request: Request):
    form = await request.form()
    username = form.get("username", "")
    email = form.get("email", "")
    password = form.get("password", "")

    if not username or not email or not password:
        return RedirectResponse("/register?error=Please+fill+all+fields", status_code=302)

    import secrets

    token = secrets.token_hex(16)
    _sessions[token] = {"username": str(username), "role": "viewer"}

    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("session", token, httponly=True)
    return response


@ui.page("/dashboard")
@protected(get_current_user, redirect_to="/login")
async def dashboard(request: Request):
    user = request.state.user
    return Page(
        Nav(
            Div(
                A("Dashboard", href="/dashboard", cls="text-lg font-bold"),
                cls="flex-1",
            ),
            UserMenu(
                username=user["username"],
                logout_url="/logout",
                menu_items=[("Admin", "/admin/")],
            ),
            cls="navbar bg-base-200 px-4",
        ),
        Div(
            Card(
                H1(f"Welcome, {user['username']}!"),
                Div(f"Role: {user['role']}", cls="text-sm opacity-70"),
                title="Dashboard",
            ),
            RoleGuard(
                Card(
                    "You have admin access. ",
                    A("Go to Admin Panel", href="/admin/", cls="link link-primary"),
                    title="Admin Access",
                ),
                role="admin",
                user_role=user["role"],
            ),
            RoleGuard(
                Card(
                    "Editor tools would appear here.",
                    title="Editor Tools",
                ),
                role=["admin", "editor"],
                user_role=user["role"],
            ),
            cls="container mx-auto p-6 space-y-4",
        ),
        title="Dashboard",
    )


@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session")
    if token and token in _sessions:
        del _sessions[token]
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("session")
    return response


# ---------- Admin Site (with auth) ----------

admin = AdminSite(
    app,
    prefix="/admin",
    title="kokage Admin",
    auth_check=get_current_user,
)

admin.register(
    User,
    storage=user_storage,
    icon="U",
    search_fields=["name", "email"],
    filters={
        "role": ColumnFilter(
            type="select",
            options=[("admin", "Admin"), ("editor", "Editor"), ("viewer", "Viewer")],
        ),
    },
)
admin.register(
    Article,
    storage=article_storage,
    icon="A",
    search_fields=["title", "author"],
    filters={
        "status": ColumnFilter(
            type="select",
            options=[("draft", "Draft"), ("published", "Published")],
        ),
    },
)
