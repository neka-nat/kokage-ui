# Real-time Notifications

A demo of SSE-based real-time notifications with multiple pages communicating in real time.

## Run

```bash
uvicorn examples.realtime:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in one tab, and [http://localhost:8000/monitor](http://localhost:8000/monitor) in another tab.

## Code

```python
--8<-- "examples/realtime.py"
```

## Features Demonstrated

- **Notifier** — Server-side SSE notification dispatcher with channel management
- **NotificationStream** — Client-side toast display from SSE events
- **AutoRefresh** — Live connection stats updated every 2 seconds
- **DarkModeToggle** — Theme toggle in navbar

## Key Patterns

### Server-Side: Notifier

```python
notifier = Notifier()
notifier.register_routes(app)  # GET /notifications/{channel}

# Send to a specific channel
await notifier.send("alerts", "Hello!", level="success")

# Broadcast to all channels
await notifier.send("all", "Broadcast message", level="info")
```

### Client-Side: NotificationStream

```python
Page(
    NotificationStream(channel="alerts"),  # Hidden SSE listener
    H1("Dashboard"),
    include_toast=True,
)
```

The component renders a hidden `<div>` with an inline script that opens an `EventSource` connection and displays incoming notifications as DaisyUI toast alerts.

### Multi-Tab Communication

1. **Send page** (`/`) — Buttons trigger `POST /api/notify` to push notifications
2. **Monitor page** (`/monitor`) — Listens on `"alerts"` channel, shows toast alerts
3. **Live Feed page** (`/feed`) — AutoRefresh polls `/api/feed` for message history

All pages that include `NotificationStream(channel="alerts")` receive notifications in real time.
