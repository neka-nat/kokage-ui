# Pages & Layout

## Page

`Page` generates a complete `<!DOCTYPE html>` document. It automatically includes:

- htmx (locally bundled)
- DaisyUI CSS (CDN)
- Tailwind CSS (CDN)

```python
from kokage_ui import Page, H1, P

Page(
    H1("Hello"),
    P("World"),
    title="My Page",
    theme="light",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Components to place in `<body>` |
| `title` | str | Page title (`<title>` tag) |
| `theme` | str | DaisyUI theme name (default: `"light"`) |
| `head_extra` | list | Additional elements for `<head>` |
| `lang` | str | HTML `lang` attribute (default: `"ja"`) |
| `include_sse` | bool | Load htmx SSE extension |
| `include_toast` | bool | Enable toast notification support |

### Adding Custom Head Elements

```python
from kokage_ui import Page, Link, Script

Page(
    "Content",
    title="Custom Head",
    head_extra=[
        Link(rel="icon", href="/favicon.ico"),
        Script(src="/custom.js"),
    ],
)
```

### Toast Support

When `include_toast=True`, Page adds a toast container and JavaScript that reads `_toast` and `_toast_type` query parameters to display notifications. This is used by the CRUD system for success/error messages after operations.

## @ui.page() Decorator

Registers a full-page HTML route on your FastAPI app.

```python
from fastapi import FastAPI
from kokage_ui import KokageUI, Page, H1

app = FastAPI()
ui = KokageUI(app)

@ui.page("/")
def home():
    return Page(H1("Home"), title="Home")
```

The decorated function can return:

- A `Page` object
- A `Component` object
- A `str` (raw HTML)
- A list/tuple of the above

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | str | URL path |
| `methods` | list[str] \| None | HTTP methods (default: `["GET"]`) |
| `layout` | Layout \| None | Layout instance to wrap the result |
| `title` | str | Page title (used with layout) |
| `**route_kwargs` | Any | Passed to FastAPI's `add_api_route()` |

### Using with Layout

When a `layout` is provided and the function returns something other than a `Page`, the result is automatically wrapped using `layout.wrap()`:

```python
from kokage_ui import Layout, NavBar, A, Div

layout = Layout(
    navbar=NavBar(start=A("App", href="/", cls="btn btn-ghost text-xl")),
    title_suffix=" - My App",
)

@ui.page("/", layout=layout, title="Home")
def home():
    return Div("Content")  # Automatically wrapped in layout
```

## @ui.fragment() Decorator

Registers an HTML fragment route for htmx partial responses.

```python
@ui.fragment("/api/data")
def load_data():
    return Div("Loaded!")
```

By default, fragment endpoints **only accept htmx requests** (requests with the `HX-Request` header). Non-htmx requests receive a 403 response. Set `htmx_only=False` to allow all requests.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | str | URL path |
| `methods` | list[str] \| None | HTTP methods (default: `["GET"]`) |
| `htmx_only` | bool | Only allow htmx requests (default: `True`) |
| `**route_kwargs` | Any | Passed to FastAPI's `add_api_route()` |

### Accessing the Request

Fragment handlers can optionally accept a `request` parameter:

```python
from fastapi import Request

@ui.fragment("/api/search")
def search(request: Request, q: str = ""):
    # Access query params, headers, etc.
    return Div(f"Results for: {q}")
```

## KokageUI

The main integration class. Wraps a FastAPI app and provides `page()`, `fragment()`, and `crud()` decorators.

```python
from fastapi import FastAPI
from kokage_ui import KokageUI

app = FastAPI()
ui = KokageUI(app, prefix="/_kokage")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | FastAPI | FastAPI application instance |
| `prefix` | str | URL prefix for static files (default: `"/_kokage"`) |

### What It Does

- Mounts the bundled `htmx.min.js` at `{prefix}/static/htmx.min.js`
- Provides `@ui.page()` for full-page routes
- Provides `@ui.fragment()` for htmx partial routes
- Provides `ui.crud()` for auto-generated CRUD routes
