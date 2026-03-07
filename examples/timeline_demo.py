"""Timeline demo — project history & activity log."""

from fastapi import FastAPI

from kokage_ui import (
    Card,
    Div,
    H1,
    H2,
    KokageUI,
    Layout,
    NavBar,
    A,
    Page,
    Timeline,
    TimelineItem,
    Badge,
)

app = FastAPI()
ui = KokageUI(app)

layout = Layout(
    navbar=NavBar(start=A("Timeline Demo", href="/", cls="btn btn-ghost text-xl")),
    title_suffix=" - Timeline Demo",
)


@ui.page("/", layout=layout, title="Timeline")
def index():
    return Div(
        H1("Timeline Component Demo", cls="text-3xl font-bold mb-8"),
        # Project history
        H2("Project History", cls="text-2xl font-semibold mb-4"),
        Timeline(items=[
            TimelineItem(
                "プロジェクト開始",
                label="2024-01-01",
                color="primary",
            ),
            TimelineItem(
                "v1.0 リリース",
                label="2024-03-15",
                color="success",
            ),
            TimelineItem(
                "v1.5 マイナーアップデート",
                label="2024-06-01",
                color="info",
            ),
            TimelineItem(
                "v2.0 開発中",
                label="2024-09-01",
            ),
        ], cls="mb-12"),

        # Activity log (compact)
        H2("Activity Log (Compact)", cls="text-2xl font-semibold mb-4"),
        Timeline(items=[
            TimelineItem(
                Div(
                    Badge("Deploy", color="success", size="sm"),
                    " Production deploy completed",
                    cls="flex items-center gap-2",
                ),
                label="10:30",
                color="success",
            ),
            TimelineItem(
                Div(
                    Badge("Review", color="info", size="sm"),
                    " PR #42 approved",
                    cls="flex items-center gap-2",
                ),
                label="09:15",
                color="info",
            ),
            TimelineItem(
                Div(
                    Badge("Commit", color="primary", size="sm"),
                    " Added timeline component",
                    cls="flex items-center gap-2",
                ),
                label="08:00",
                color="primary",
            ),
        ], compact=True, cls="mb-12"),

        # Horizontal timeline
        H2("Horizontal Timeline", cls="text-2xl font-semibold mb-4"),
        Timeline(items=[
            TimelineItem("Step 1", label="Plan", color="primary"),
            TimelineItem("Step 2", label="Build", color="primary"),
            TimelineItem("Step 3", label="Test", color="accent"),
            TimelineItem("Step 4", label="Deploy"),
        ], vertical=False),
        cls="container mx-auto p-8",
    )
