# Real-time Notifications

kokage-ui provides an SSE-based notification system for pushing real-time toast alerts to connected clients.

## Quick Start

```python
from fastapi import FastAPI
from kokage_ui import KokageUI, Notifier, NotificationStream, Page, H1

app = FastAPI()
ui = KokageUI(app)

notifier = Notifier()
notifier.register_routes(app)  # GET /notifications/{channel}

@ui.page("/dashboard")
def dashboard():
    return Page(
        NotificationStream(channel="admin"),
        H1("Dashboard"),
        title="Dashboard",
    )

@app.post("/action")
async def do_action():
    await notifier.send("admin", "Action completed!", level="success")
    return {"ok": True}
```

## Notifier

Server-side notification dispatcher. Manages channels of connected SSE clients.

```python
notifier = Notifier(default_channel="default")
```

### Sending Notifications

```python
# Send to a specific channel
await notifier.send("admin", "New user registered", level="info")

# Send to all channels
await notifier.send("all", "System update complete", level="success")
await notifier.send_all("Maintenance in 5 minutes", level="warning")
```

| Level | Description |
|-------|-------------|
| `"info"` | Blue info alert (default) |
| `"success"` | Green success alert |
| `"warning"` | Yellow warning alert |
| `"error"` | Red error alert |

### Channel Management

```python
notifier.active_channels    # ["admin", "users"] — channels with listeners
notifier.client_count()     # 5 — total connected clients
notifier.client_count("admin")  # 2 — clients on specific channel
```

Channels are created lazily when clients connect and removed when the last client disconnects. Sending to a channel with no listeners is a no-op.

### Route Registration

```python
# Default: GET /notifications/{channel}
notifier.register_routes(app)

# Custom path
notifier.register_routes(app, path="/sse/{channel}")
```

Or manually register the endpoint:

```python
@app.get("/notifications/{channel}")
async def notifications(request: Request, channel: str):
    return await notifier.sse_endpoint(request, channel)
```

## NotificationStream

Client-side component that listens for SSE notifications and displays them as DaisyUI toasts.

```python
NotificationStream(channel="admin")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel` | str | Channel to subscribe to (default: `"default"`) |
| `url` | str \| None | Explicit SSE URL (default: `/notifications/{channel}`) |
| `position` | str | Toast position (default: `"toast-end toast-top"`) |
| `dismiss_ms` | int | Auto-dismiss delay in ms (default: 3000) |

### Custom Position and Timing

```python
NotificationStream(
    channel="alerts",
    position="toast-start toast-bottom",
    dismiss_ms=5000,
)
```

## How It Works

1. `NotificationStream` renders a hidden `<div>` with an inline `<script>`
2. The script opens an `EventSource` connection to the SSE endpoint
3. When `notifier.send()` is called, the message is pushed to all connected clients via `asyncio.Queue`
4. The client JS creates a DaisyUI toast alert, appends it to `document.body`, and auto-removes after `dismiss_ms`
5. Connection keepalive is maintained with 15-second heartbeat comments
6. Reconnection is handled automatically by the browser's `EventSource` API
