"""kokage-ui: Admin dashboard demo.

Run:
    uv run uvicorn examples.admin_demo:app --reload

Open http://localhost:8000 in your browser.

Features demonstrated:
    - AdminSite (auto-generated admin panel)
    - Dashboard charts and activity log
    - Custom dashboard widgets
    - Column filters and custom bulk actions
    - InMemoryStorage with multiple models
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from kokage_ui import (
    AdminSite,
    Card,
    Chart,
    ChartData,
    ColumnFilter,
    Dataset,
    InMemoryStorage,
)

app = FastAPI()

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

user_storage = InMemoryStorage(
    User,
    initial=[
        User(id="1", name="Admin User", email="admin@example.com", role="admin"),
        User(id="2", name="Tanaka Taro", email="tanaka@example.com", role="editor"),
        User(id="3", name="Suzuki Hanako", email="suzuki@example.com", role="viewer"),
    ],
)

product_storage = InMemoryStorage(
    Product,
    initial=[
        Product(id="1", name="Laptop", price=999.99, category="Electronics"),
        Product(id="2", name="Desk Chair", price=249.50, category="Furniture"),
        Product(id="3", name="Python Book", price=39.99, category="Books", in_stock=False),
        Product(id="4", name="Monitor", price=449.00, category="Electronics"),
    ],
)

order_storage = InMemoryStorage(
    Order,
    initial=[
        Order(id="1", product="Laptop", quantity=2, status="shipped"),
        Order(id="2", product="Desk Chair", quantity=1, status="pending"),
        Order(id="3", product="Python Book", quantity=5, status="delivered"),
    ],
)


# ---------- Custom Dashboard Widgets ----------


def product_category_chart(items, total):
    """Show product count by category as a pie chart."""
    categories: dict[str, int] = {}
    for item in items:
        cat = item.category or "Other"
        categories[cat] = categories.get(cat, 0) + 1

    return Card(
        Chart(
            type="doughnut",
            data=ChartData(
                labels=list(categories.keys()),
                datasets=[
                    Dataset(
                        data=list(categories.values()),
                        backgroundColor=["#36a2eb", "#ff6384", "#ffce56", "#4bc0c0", "#9966ff"],
                    ),
                ],
            ),
            options={"plugins": {"legend": {"position": "bottom"}}},
            height="200px",
        ),
        title="Products by Category",
    )


def order_status_chart(items, total):
    """Show order status distribution as a bar chart."""
    statuses: dict[str, int] = {}
    for item in items:
        statuses[item.status] = statuses.get(item.status, 0) + 1

    colors = {"pending": "#ffce56", "shipped": "#36a2eb", "delivered": "#4bc0c0"}

    return Card(
        Chart(
            type="bar",
            data=ChartData(
                labels=list(statuses.keys()),
                datasets=[
                    Dataset(
                        label="Orders",
                        data=list(statuses.values()),
                        backgroundColor=[colors.get(s, "#9966ff") for s in statuses],
                    ),
                ],
            ),
            options={
                "plugins": {"legend": {"display": False}},
                "scales": {"y": {"beginAtZero": True}},
            },
            height="200px",
        ),
        title="Orders by Status",
    )


# ---------- Custom Bulk Actions ----------


async def deactivate_users(selected_ids, storage):
    """Deactivate selected users."""
    for uid in selected_ids:
        item = await storage.get(uid)
        if item:
            updated = item.model_copy(update={"is_active": False})
            await storage.update(uid, updated)


async def mark_shipped(selected_ids, storage):
    """Mark selected orders as shipped."""
    for oid in selected_ids:
        item = await storage.get(oid)
        if item:
            updated = item.model_copy(update={"status": "shipped"})
            await storage.update(oid, updated)


# ---------- Admin Site ----------

admin = AdminSite(app, prefix="/admin", title="kokage Admin")

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
    actions=[("Deactivate Selected", deactivate_users)],
)
admin.register(
    Product,
    storage=product_storage,
    icon="P",
    search_fields=["name", "category"],
    filters={
        "category": ColumnFilter(
            type="select",
            options=[
                ("Electronics", "Electronics"),
                ("Furniture", "Furniture"),
                ("Books", "Books"),
            ],
        ),
    },
    dashboard_widgets=[product_category_chart],
)
admin.register(
    Order,
    storage=order_storage,
    icon="O",
    list_fields=["product", "quantity", "status"],
    filters={
        "status": ColumnFilter(
            type="select",
            options=[
                ("pending", "Pending"),
                ("shipped", "Shipped"),
                ("delivered", "Delivered"),
            ],
        ),
    },
    actions=[("Mark as Shipped", mark_shipped)],
    dashboard_widgets=[order_status_chart],
)
