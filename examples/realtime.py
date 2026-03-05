"""kokage-ui: Real-time notification demo.

Run:
    uv run uvicorn examples.realtime:app --reload

Open http://localhost:8000 in your browser.
Open a second tab at http://localhost:8000/monitor to see notifications.

Features demonstrated:
    - Notifier (server-side SSE push)
    - NotificationStream (client-side toast display)
    - AutoRefresh (polling)
    - SSEStream (htmx SSE extension)
    - DarkModeToggle
"""

import random
from datetime import datetime

from fastapi import FastAPI, Request

from kokage_ui import (
    A,
    AutoRefresh,
    Card,
    DaisyButton,
    DarkModeToggle,
    Div,
    H1,
    H2,
    KokageUI,
    NavBar,
    NotificationStream,
    Notifier,
    P,
    Page,
    Span,
    Stat,
    Stats,
)

app = FastAPI()
ui = KokageUI(app)

# ---------- Notifier ----------

notifier = Notifier()
notifier.register_routes(app)  # GET /notifications/{channel}

# ---------- Layout ----------


def _navbar():
    return NavBar(
        start=A("Real-time Demo", cls="btn btn-ghost text-xl", href="/"),
        end=Div(
            A("Send", cls="btn btn-ghost btn-sm", href="/"),
            A("Monitor", cls="btn btn-ghost btn-sm", href="/monitor"),
            A("Live Feed", cls="btn btn-ghost btn-sm", href="/feed"),
            DarkModeToggle(),
            cls="flex items-center gap-2",
        ),
    )


def _page(content, title, channel=None, include_sse=False):
    children = [_navbar()]
    if channel:
        children.append(NotificationStream(channel=channel))
    children.append(Div(content, cls="container mx-auto p-6"))

    return Page(
        *children,
        title=f"{title} - Real-time Demo",
        include_toast=True,
        include_sse=include_sse,
    )


# ---------- Send Page ----------


@ui.page("/")
def send_page():
    return _page(
        Div(
            H1("Send Notifications", cls="text-3xl font-bold mb-6"),
            P(
                "Click the buttons below to send notifications. "
                "Open the Monitor page in another tab to receive them.",
                cls="mb-6 text-base-content/70",
            ),
            # Notification buttons
            Div(
                Card(
                    P("Send a notification to the 'alerts' channel."),
                    actions=[
                        DaisyButton(
                            "Info",
                            color="info",
                            hx_post="/api/notify?level=info",
                            hx_swap="none",
                        ),
                        DaisyButton(
                            "Success",
                            color="success",
                            hx_post="/api/notify?level=success",
                            hx_swap="none",
                        ),
                        DaisyButton(
                            "Warning",
                            color="warning",
                            hx_post="/api/notify?level=warning",
                            hx_swap="none",
                        ),
                        DaisyButton(
                            "Error",
                            color="error",
                            hx_post="/api/notify?level=error",
                            hx_swap="none",
                        ),
                    ],
                    title="Send to Alerts Channel",
                ),
                Card(
                    P("Broadcast a notification to all connected clients."),
                    actions=[
                        DaisyButton(
                            "Broadcast",
                            color="primary",
                            hx_post="/api/broadcast",
                            hx_swap="none",
                        ),
                    ],
                    title="Broadcast to All",
                ),
                cls="grid grid-cols-1 md:grid-cols-2 gap-6",
            ),
            # Connection stats (auto-refresh)
            H2("Connection Stats", cls="text-2xl font-bold mt-8 mb-4"),
            AutoRefresh(
                Span("Loading...", cls="loading loading-spinner"),
                url="/api/conn-stats",
                interval=2,
            ),
        ),
        title="Send",
        channel="alerts",  # This page also receives notifications
    )


# ---------- Monitor Page ----------


@ui.page("/monitor")
def monitor_page():
    return _page(
        Div(
            H1("Notification Monitor", cls="text-3xl font-bold mb-6"),
            P(
                "This page listens on the 'alerts' channel. "
                "Notifications will appear as toast alerts in the top-right corner.",
                cls="mb-6 text-base-content/70",
            ),
            Card(
                P("Waiting for notifications..."),
                P(
                    "Go to the Send page and click a button to trigger a notification.",
                    cls="text-sm text-base-content/60",
                ),
                title="Listening on 'alerts' channel",
            ),
            # Auto-refreshing stats
            H2("Live Stats", cls="text-2xl font-bold mt-8 mb-4"),
            AutoRefresh(
                Span("Loading...", cls="loading loading-spinner"),
                url="/api/conn-stats",
                interval=2,
            ),
        ),
        title="Monitor",
        channel="alerts",
    )


# ---------- Live Feed Page ----------

# Store recent messages for the feed
_recent_messages: list[dict] = []


@ui.page("/feed")
def feed_page():
    return _page(
        Div(
            H1("Live Feed", cls="text-3xl font-bold mb-6"),
            P("Messages update automatically every 2 seconds.", cls="mb-6 text-base-content/70"),
            AutoRefresh(
                Span("Loading...", cls="loading loading-spinner"),
                url="/api/feed",
                interval=2,
            ),
        ),
        title="Live Feed",
        channel="alerts",
    )


# ---------- API Endpoints ----------

MESSAGES = [
    "Server health check passed",
    "New user signed up",
    "Order #1234 placed",
    "Deployment completed",
    "Cache cleared",
    "Database backup finished",
    "API rate limit reached",
    "Payment processed",
]


@app.post("/api/notify")
async def send_notification(level: str = "info"):
    message = random.choice(MESSAGES)
    count = await notifier.send("alerts", message, level=level)
    # Track for feed
    _recent_messages.insert(0, {
        "message": message,
        "level": level,
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    if len(_recent_messages) > 20:
        _recent_messages.pop()
    return {"sent_to": count, "message": message}


@app.post("/api/broadcast")
async def broadcast_notification():
    message = "Broadcast: " + random.choice(MESSAGES)
    count = await notifier.send("all", message, level="info")
    _recent_messages.insert(0, {
        "message": message,
        "level": "info",
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    if len(_recent_messages) > 20:
        _recent_messages.pop()
    return {"sent_to": count, "message": message}


@ui.fragment("/api/conn-stats")
def conn_stats(request: Request):
    channels = notifier.active_channels
    return Stats(
        Stat(title="Active Channels", value=str(len(channels))),
        Stat(title="Total Clients", value=str(notifier.client_count())),
        Stat(title="Messages Sent", value=str(len(_recent_messages))),
    )


@ui.fragment("/api/feed")
def feed_fragment(request: Request):
    if not _recent_messages:
        return P("No messages yet. Send a notification to see it here.", cls="text-base-content/60")

    cards = []
    level_colors = {"info": "info", "success": "success", "warning": "warning", "error": "error"}
    for msg in _recent_messages[:10]:
        color = level_colors.get(msg["level"], "info")
        cards.append(
            Div(
                Div(
                    Span(msg["time"], cls="text-xs text-base-content/50 font-mono"),
                    Span(msg["level"].upper(), cls=f"badge badge-{color} badge-sm"),
                    cls="flex items-center gap-2 mb-1",
                ),
                P(msg["message"]),
                cls="border-b border-base-200 pb-3 mb-3",
            )
        )
    return Div(*cards)
