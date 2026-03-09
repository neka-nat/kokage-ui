"""kokage-ui: Chart.js demo with multiple chart types and interactive updates.

Run:
    uv run uvicorn examples.chart_demo:app --reload

Open http://localhost:8000 in your browser.

Features demonstrated:
    - Chart component with typed ChartData / Dataset models
    - htmx fragment for dynamic chart updates
    - Card layout, NavBar, Tabs
    - DarkModeToggle, ThemeSwitcher
"""

import random

from fastapi import FastAPI

from kokage_ui import (
    A,
    Card,
    Chart,
    ChartData,
    ChartOptions,
    DaisyButton,
    DarkModeToggle,
    Dataset,
    Div,
    H1,
    H2,
    KokageUI,
    NavBar,
    P,
    Page,
    Tab,
    Tabs,
    ThemeSwitcher,
)

app = FastAPI()
ui = KokageUI(app)

# ---------- Sample Data ----------

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SALES = [120, 190, 150, 220, 280, 250, 310, 340, 290, 380, 420, 460]
COSTS = [80, 110, 95, 140, 160, 150, 180, 200, 170, 220, 250, 270]
PROFIT = [s - c for s, c in zip(SALES, COSTS)]

CATEGORIES = ["Electronics", "Clothing", "Food", "Books", "Sports"]
CATEGORY_SALES = [340, 280, 220, 180, 150]

SKILLS = ["Python", "JavaScript", "SQL", "DevOps", "Design"]
TEAM_A = [90, 60, 80, 70, 50]
TEAM_B = [70, 85, 65, 60, 75]


# ---------- Charts ----------


def line_chart():
    return Chart(
        type="line",
        data=ChartData(
            labels=MONTHS,
            datasets=[
                Dataset(
                    label="Sales",
                    data=SALES,
                    borderColor="#36a2eb",
                    backgroundColor="rgba(54,162,235,0.1)",
                    fill=True,
                    tension=0.3,
                ),
                Dataset(
                    label="Costs",
                    data=COSTS,
                    borderColor="#ff6384",
                    backgroundColor="rgba(255,99,132,0.1)",
                    fill=True,
                    tension=0.3,
                ),
                Dataset(
                    label="Profit",
                    data=PROFIT,
                    borderColor="#4bc0c0",
                    borderDash=[5, 5],
                    fill=False,
                    tension=0.3,
                ),
            ],
        ),
        options=ChartOptions(
            plugins={"title": {"display": True, "text": "Monthly Sales & Costs"}},
            scales={"y": {"beginAtZero": True}},
        ),
        height="350px",
    )


def bar_chart():
    return Chart(
        type="bar",
        data=ChartData(
            labels=MONTHS,
            datasets=[
                Dataset(label="Sales", data=SALES, backgroundColor="#36a2eb"),
                Dataset(label="Costs", data=COSTS, backgroundColor="#ff6384"),
            ],
        ),
        options=ChartOptions(
            plugins={"title": {"display": True, "text": "Monthly Comparison"}},
            scales={"y": {"beginAtZero": True}},
        ),
        height="350px",
    )


def pie_chart():
    return Chart(
        type="pie",
        data=ChartData(
            labels=CATEGORIES,
            datasets=[
                Dataset(
                    data=CATEGORY_SALES,
                    backgroundColor=["#36a2eb", "#ff6384", "#ffce56", "#4bc0c0", "#9966ff"],
                ),
            ],
        ),
        options=ChartOptions(
            plugins={"title": {"display": True, "text": "Sales by Category"}},
        ),
        height="350px",
    )


def doughnut_chart():
    return Chart(
        type="doughnut",
        data=ChartData(
            labels=CATEGORIES,
            datasets=[
                Dataset(
                    data=CATEGORY_SALES,
                    backgroundColor=["#36a2eb", "#ff6384", "#ffce56", "#4bc0c0", "#9966ff"],
                ),
            ],
        ),
        options=ChartOptions(
            plugins={"title": {"display": True, "text": "Category Distribution"}},
        ),
        height="350px",
    )


def radar_chart():
    return Chart(
        type="radar",
        data=ChartData(
            labels=SKILLS,
            datasets=[
                Dataset(
                    label="Team A",
                    data=TEAM_A,
                    borderColor="#36a2eb",
                    backgroundColor="rgba(54,162,235,0.2)",
                ),
                Dataset(
                    label="Team B",
                    data=TEAM_B,
                    borderColor="#ff6384",
                    backgroundColor="rgba(255,99,132,0.2)",
                ),
            ],
        ),
        options=ChartOptions(
            plugins={"title": {"display": True, "text": "Team Skill Comparison"}},
            scales={"r": {"beginAtZero": True, "max": 100}},
        ),
        height="350px",
    )


def scatter_chart():
    random.seed(42)
    points_a = [{"x": random.randint(20, 90), "y": random.randint(30, 95)} for _ in range(20)]
    points_b = [{"x": random.randint(10, 80), "y": random.randint(20, 85)} for _ in range(20)]
    return Chart(
        type="scatter",
        data=ChartData(
            datasets=[
                Dataset(label="Group A", data=points_a, backgroundColor="#36a2eb"),
                Dataset(label="Group B", data=points_b, backgroundColor="#ff6384"),
            ],
        ),
        options=ChartOptions(
            plugins={"title": {"display": True, "text": "Scatter Plot"}},
            scales={
                "x": {"beginAtZero": True, "title": {"display": True, "text": "X Value"}},
                "y": {"beginAtZero": True, "title": {"display": True, "text": "Y Value"}},
            },
        ),
        height="350px",
    )


# ---------- Layout ----------


def _navbar():
    return NavBar(
        start=A("Chart Demo", cls="btn btn-ghost text-xl", href="/"),
        end=Div(
            DarkModeToggle(),
            ThemeSwitcher(
                themes=["light", "dark", "nord", "dracula", "corporate"],
                size="sm",
            ),
            cls="flex items-center gap-2",
        ),
    )


# ---------- Routes ----------


@ui.page("/")
def index():
    tabs = Tabs(
        tabs=[
            Tab(
                label="Line",
                content=Card(line_chart(), title="Line Chart"),
                active=True,
            ),
            Tab(label="Bar", content=Card(bar_chart(), title="Bar Chart")),
            Tab(label="Pie", content=Card(pie_chart(), title="Pie Chart")),
            Tab(label="Doughnut", content=Card(doughnut_chart(), title="Doughnut Chart")),
            Tab(label="Radar", content=Card(radar_chart(), title="Radar Chart")),
            Tab(label="Scatter", content=Card(scatter_chart(), title="Scatter Chart")),
        ],
        variant="boxed",
    )

    return Page(
        _navbar(),
        Div(
            H1("Chart.js Demo", cls="text-3xl font-bold mb-2"),
            P("Various chart types powered by kokage-ui's Chart component.", cls="text-base-content/70 mb-6"),
            tabs,
            Div(
                H2("Live Update", cls="text-2xl font-bold mb-4"),
                P("Click the button to generate a chart with random data.", cls="text-base-content/70 mb-4"),
                DaisyButton(
                    "Generate Random Chart",
                    color="primary",
                    hx_get="/random-chart",
                    hx_target="#random-chart-container",
                    hx_swap="innerHTML",
                ),
                Div(id="random-chart-container", cls="mt-4"),
                cls="mt-8",
            ),
            cls="container mx-auto p-6",
        ),
        title="Chart Demo - kokage-ui",
        include_chartjs=True,
    )


@ui.fragment("/random-chart")
def random_chart():
    labels = [f"Item {i + 1}" for i in range(8)]
    data = [random.randint(10, 100) for _ in range(8)]
    colors = [f"hsl({random.randint(0, 360)}, 70%, 60%)" for _ in range(8)]
    chart_type = random.choice(["bar", "line", "doughnut", "pie", "radar"])

    bg = "rgba(54,162,235,0.2)" if chart_type == "radar" else colors
    border = "#36a2eb" if chart_type == "radar" else colors

    return Card(
        Chart(
            type=chart_type,
            data=ChartData(
                labels=labels,
                datasets=[
                    Dataset(
                        label="Random Data",
                        data=data,
                        backgroundColor=bg,
                        borderColor=border,
                    ),
                ],
            ),
            options=ChartOptions(
                plugins={"title": {"display": True, "text": f"Random {chart_type.title()} Chart"}},
            ),
            height="350px",
        ),
        title=f"Random {chart_type.title()} Chart",
    )
