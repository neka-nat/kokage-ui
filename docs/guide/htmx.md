# htmx Patterns

kokage-ui includes ready-made components for common htmx interaction patterns. htmx is bundled locally — no CDN needed.

## AutoRefresh

Polls a URL at a regular interval and replaces its content.

```python
from kokage_ui import AutoRefresh, Span

AutoRefresh(
    Span("Loading...", cls="loading loading-spinner"),
    url="/api/stats",
    interval=3,
)
```

This renders a `<div>` with `hx-get="/api/stats"` and `hx-trigger="every 3s"`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Initial content (shown before first load) |
| `url` | str | URL to poll |
| `interval` | int | Refresh interval in seconds (default: 5) |
| `target` | str \| None | Target selector (default: self) |
| `swap` | str | Swap method (default: `"innerHTML"`) |

### Example: Live Stats

```python
@ui.page("/")
def home():
    return Page(
        AutoRefresh(
            Span("Loading..."),
            url="/api/stats",
            interval=3,
        ),
        title="Dashboard",
    )

@ui.fragment("/api/stats")
def stats(request: Request):
    return Stats(
        Stat(title="Users", value=str(get_user_count())),
        Stat(title="CPU", value=f"{get_cpu()}%"),
    )
```

## SearchFilter

An input that triggers server-side search on keyup with debounce.

```python
from kokage_ui import SearchFilter

SearchFilter(
    url="/api/search",
    target="#results",
    placeholder="Search users...",
    delay=300,
)
```

This renders an `<input type="search">` with `hx-get` and `hx-trigger="keyup changed delay:300ms"`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | Search endpoint URL |
| `target` | str | CSS selector for results container |
| `placeholder` | str | Input placeholder (default: `"Search..."`) |
| `name` | str | Input name attribute (default: `"q"`) |
| `delay` | int | Debounce delay in ms (default: 300) |

### Example: Live Search

```python
@ui.page("/")
def home():
    return Page(
        SearchFilter(url="/api/users/search", target="#user-table"),
        Div(id="user-table"),
        title="Search",
    )

@ui.fragment("/api/users/search")
def search(request: Request, q: str = ""):
    filtered = [u for u in users if q.lower() in u.name.lower()] if q else users
    return DaisyTable(
        headers=["Name", "Email"],
        rows=[[u.name, u.email] for u in filtered],
    )
```

## InfiniteScroll

Loads more content when the element scrolls into view.

```python
from kokage_ui import InfiniteScroll

InfiniteScroll(
    url="/api/items?page=2",
    target="#item-list",
    swap="beforeend",
)
```

This renders a `<div>` with `hx-trigger="revealed"` — htmx loads the URL when the element enters the viewport.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | Next page URL |
| `target` | str \| None | Insert target selector |
| `swap` | str | Swap method (default: `"beforeend"`) |
| `indicator` | Any | Custom loading indicator (default: spinner) |

### Example: Paginated List

```python
@ui.fragment("/api/items")
def items(request: Request, page: int = 1):
    items = get_items(page=page)
    result = [Div(item.name) for item in items]
    if has_more(page):
        result.append(InfiniteScroll(url=f"/api/items?page={page + 1}"))
    return result
```

## SSEStream

Receives Server-Sent Events for real-time updates. Requires the htmx SSE extension.

```python
from kokage_ui import SSEStream, Page

Page(
    SSEStream(
        "Waiting for events...",
        url="/api/events",
        event="update",
    ),
    title="Live Feed",
    include_sse=True,  # Required!
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Initial content |
| `url` | str | SSE endpoint URL |
| `event` | str | SSE event name to listen for (default: `"message"`) |
| `swap` | str | Swap method (default: `"innerHTML"`) |

!!! important
    You must set `include_sse=True` on the `Page` (or `Layout`) to load the htmx SSE extension.

### Example: SSE Endpoint

```python
from sse_starlette.sse import EventSourceResponse

@app.get("/api/events")
async def events():
    async def generate():
        while True:
            data = get_latest_data()
            yield {"event": "update", "data": f"<div>{data}</div>"}
            await asyncio.sleep(1)
    return EventSourceResponse(generate())
```

## ConfirmDelete

A delete button that shows a confirmation dialog before sending an `hx-delete` request.

```python
from kokage_ui import ConfirmDelete

ConfirmDelete(
    "Delete",
    url="/api/items/123",
    confirm_message="Are you sure you want to delete this item?",
    target="#item-123",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Button text |
| `url` | str | DELETE endpoint URL |
| `confirm_message` | str | Confirmation dialog message (default: `"Are you sure?"`) |
| `target` | str \| None | Target selector to update after deletion |
| `swap` | str | Swap method (default: `"outerHTML"`) |

The default styling is `btn btn-error btn-outline`.

## HxSwapOOB

Out-of-Band Swap — updates elements outside the main htmx target.

```python
from kokage_ui import HxSwapOOB

# Return from a fragment to update multiple elements
@ui.fragment("/api/action", methods=["POST"])
def action(request: Request):
    return [
        Div("Main content updated"),
        HxSwapOOB(
            Span("42", cls="badge"),
            target_id="notification-count",
        ),
    ]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Content to insert |
| `target_id` | str | ID of the element to update |
| `swap` | str | Swap method (default: `"true"` = innerHTML) |

This renders a `<div id="notification-count" hx-swap-oob="true">` that htmx will use to update the element with that ID, regardless of the main target.

## DependentField

A field that updates when another field changes, using htmx to fetch new options from the server.

```python
from kokage_ui import DependentField

DependentField(
    url="/api/cities",
    trigger_name="country",
    target="#city-select",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | Endpoint to fetch updated content |
| `trigger_name` | str | Name of the field that triggers the update |
| `target` | str | CSS selector of the element to update |

### Example: Country → City Cascade

```python
@ui.page("/")
def form():
    return Page(
        Form(
            DaisySelect(
                "Country", name="country",
                options=[("us", "US"), ("jp", "Japan")],
                hx_get="/api/cities", hx_target="#city-select",
            ),
            Div(id="city-select"),
        ),
    )

@ui.fragment("/api/cities")
def cities(country: str = ""):
    city_map = {"us": ["New York", "LA"], "jp": ["Tokyo", "Osaka"]}
    options = [(c, c) for c in city_map.get(country, [])]
    return DaisySelect("City", name="city", options=options)
```

## See Also

- [Real-time Notifications](notifications.md) — SSE-based push notifications
- [DataGrid](datagrid.md) — Advanced tables with htmx-powered sort, filter, and pagination
