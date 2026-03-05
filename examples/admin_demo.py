"""kokage-ui: Admin dashboard demo with authentication.

Run:
    uv run uvicorn examples.admin_demo:app --reload

Open http://localhost:8000/login in your browser.
Login with username: admin, password: admin

Features demonstrated:
    - AdminSite (auto-generated admin panel)
    - LoginForm / UserMenu / @protected
    - ThemeSwitcher / DarkModeToggle
    - InMemoryStorage with multiple models
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from kokage_ui import (
    A,
    AdminSite,
    Card,
    DaisyButton,
    DarkModeToggle,
    Div,
    H1,
    InMemoryStorage,
    KokageUI,
    LoginForm,
    NavBar,
    P,
    Page,
    ThemeSwitcher,
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


class Product(BaseModel):
    id: str = ""
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(ge=0, default=0)
    category: str = ""
    in_stock: bool = True


class Order(BaseModel):
    id: str = ""
    product: str = ""
    quantity: int = Field(ge=1, default=1)
    status: str = "pending"


# ---------- Sample Data ----------

USERS = [
    User(id="1", name="Admin User", email="admin@example.com", role="admin", is_active=True),
    User(id="2", name="Tanaka Taro", email="tanaka@example.com", role="editor"),
    User(id="3", name="Suzuki Hanako", email="suzuki@example.com", role="viewer"),
]

PRODUCTS = [
    Product(id="1", name="Laptop", price=999.99, category="Electronics"),
    Product(id="2", name="Desk Chair", price=249.50, category="Furniture"),
    Product(id="3", name="Python Book", price=39.99, category="Books", in_stock=False),
    Product(id="4", name="Monitor", price=449.00, category="Electronics"),
]

ORDERS = [
    Order(id="1", product="Laptop", quantity=2, status="shipped"),
    Order(id="2", product="Desk Chair", quantity=1, status="pending"),
    Order(id="3", product="Python Book", quantity=5, status="delivered"),
]

user_storage = InMemoryStorage(User, initial=USERS)
product_storage = InMemoryStorage(Product, initial=PRODUCTS)
order_storage = InMemoryStorage(Order, initial=ORDERS)

# ---------- Auth ----------

# Simple cookie-based auth (for demo purposes only)
VALID_USERS = {"admin": {"username": "admin", "role": "admin"}}


def get_current_user(request: Request) -> dict | None:
    username = request.cookies.get("username")
    return VALID_USERS.get(username)


# ---------- Login / Logout ----------


@ui.page("/login")
def login_page(request: Request, error: str = ""):
    # Already logged in?
    if get_current_user(request):
        return RedirectResponse("/admin/", status_code=302)
    return Page(
        LoginForm(
            action="/login",
            error=error or None,
            title="Admin Login",
            submit_text="Sign In",
        ),
        title="Login",
    )


@app.post("/login")
async def login_handler(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    if username == "admin" and password == "admin":
        response = RedirectResponse("/admin/", status_code=302)
        response.set_cookie("username", "admin")
        return response

    return RedirectResponse("/login?error=Invalid+credentials", status_code=302)


@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("username")
    return response


# ---------- Landing Page ----------


@ui.page("/")
def home():
    return Page(
        NavBar(
            start=A("kokage Admin Demo", cls="btn btn-ghost text-xl", href="/"),
            end=Div(
                DarkModeToggle(),
                A("Login", cls="btn btn-primary btn-sm", href="/login"),
                cls="flex items-center gap-2",
            ),
        ),
        Div(
            Card(
                H1("Admin Dashboard Demo"),
                P("This demo shows AdminSite with authentication, theme switching, and multi-model management."),
                P("Login: admin / admin"),
                actions=[DaisyButton("Go to Admin", color="primary", href="/admin/")],
                title="Welcome",
            ),
            cls="container mx-auto p-8",
        ),
        title="Admin Demo",
    )


# ---------- Admin Site ----------

admin = AdminSite(
    app,
    prefix="/admin",
    title="kokage Admin",
    auth_check=get_current_user,
    theme="corporate",
    logout_url="/logout",
)

admin.register(User, storage=user_storage, icon="U", search_fields=["name", "email"])
admin.register(Product, storage=product_storage, icon="P", search_fields=["name", "category"])
admin.register(Order, storage=order_storage, icon="O", list_fields=["product", "quantity", "status"])
