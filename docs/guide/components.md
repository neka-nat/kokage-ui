# DaisyUI Components

kokage-ui provides high-level Python components that map to [DaisyUI](https://daisyui.com/) classes. These wrap low-level HTML elements with the correct class names, structure, and options.

## Card

A content container with optional title, image, and action buttons.

```python
from kokage_ui import Card, DaisyButton

Card(
    "Card content goes here.",
    title="Card Title",
    image="/photo.jpg",
    image_alt="A photo",
    actions=[DaisyButton("Action", color="primary")],
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Content for the card body |
| `title` | str \| None | Card title text |
| `image` | str \| None | Image URL (placed in `<figure>`) |
| `image_alt` | str | Image alt text |
| `actions` | list \| None | Components for card-actions area |
| `compact` | bool | Use compact card size (`card-sm`) |
| `side` | bool | Horizontal layout (`lg:card-side`) |

## Stats / Stat

Display statistics in a horizontal or vertical group.

```python
from kokage_ui import Stats, Stat

Stats(
    Stat(title="Users", value="31K", desc="+2% from last month"),
    Stat(title="Revenue", value="$4,200"),
    Stat(title="Uptime", value="99.9%"),
)
```

### Stat

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | str | Stat title (required) |
| `value` | str | Stat value (required) |
| `desc` | str \| None | Description text |
| `figure` | Any | Optional figure element |

### Stats

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Stat | Stat components |
| `vertical` | bool | Stack vertically |

## Hero

A hero banner section.

```python
from kokage_ui import Hero, H1, P, DaisyButton

Hero(
    H1("Welcome", cls="text-5xl font-bold"),
    P("Build UIs with Python.", cls="py-4"),
    DaisyButton("Get Started", color="primary"),
    min_height="60vh",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Hero content (centered) |
| `min_height` | str \| None | CSS min-height value |
| `overlay` | bool | Add hero-overlay |
| `image` | str \| None | Background image URL |

## Alert

Notification banners with variant colors.

```python
from kokage_ui import Alert

Alert("Operation completed successfully!", variant="success")
Alert("Something went wrong.", variant="error")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Alert content |
| `variant` | str | `"info"`, `"success"`, `"warning"`, `"error"` |

## Badge

Small labels for status or categories.

```python
from kokage_ui import Badge

Badge("New", color="primary")
Badge("Draft", color="ghost", outline=True)
Badge("SM", color="info", size="sm")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Badge text |
| `color` | str \| None | `primary`, `secondary`, `accent`, `info`, `success`, `warning`, `error`, `ghost`, `neutral` |
| `outline` | bool | Outline style |
| `size` | str \| None | `xs`, `sm`, `md`, `lg` |

## NavBar

Top navigation bar with start, center, and end sections.

```python
from kokage_ui import NavBar, A, Div

NavBar(
    start=A("My App", cls="btn btn-ghost text-xl", href="/"),
    end=Div(
        A("Home", cls="btn btn-ghost", href="/"),
        A("About", cls="btn btn-ghost", href="/about"),
    ),
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `start` | Any | Content for navbar-start |
| `center` | Any | Content for navbar-center |
| `end` | Any | Content for navbar-end |

## DaisyButton

Styled button with color, variant, and size options.

```python
from kokage_ui import DaisyButton

DaisyButton("Click", color="primary")
DaisyButton("Delete", color="error", variant="outline")
DaisyButton("Small", color="accent", size="sm")
DaisyButton("Loading...", color="primary", loading=True)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Button text |
| `color` | str \| None | `primary`, `secondary`, `accent`, `info`, `success`, `warning`, `error`, `neutral`, `ghost`, `link` |
| `variant` | str \| None | `outline`, `ghost`, `soft`, `link` |
| `size` | str \| None | `xs`, `sm`, `md`, `lg` |
| `loading` | bool | Show loading spinner |
| `disabled` | bool | Disable the button |

## DaisyInput

Form input with label, wrapped in DaisyUI form-control structure.

```python
from kokage_ui import DaisyInput

DaisyInput(label="Email", type="email", name="email", placeholder="you@example.com")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | str \| None | Label text |
| `type` | str | Input type (default: `"text"`) |
| `name` | str | Input name attribute |
| `placeholder` | str | Placeholder text |
| `bordered` | bool | Bordered style (default: True) |
| `required` | bool | Mark as required |

## DaisySelect

Dropdown select with label.

```python
from kokage_ui import DaisySelect

DaisySelect(
    label="Role",
    name="role",
    options=[("admin", "Admin"), ("editor", "Editor"), ("viewer", "Viewer")],
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `options` | list | List of `(value, label)` tuples or strings |
| `label` | str \| None | Label text |
| `name` | str | Select name attribute |
| `bordered` | bool | Bordered style (default: True) |

## DaisyTextarea

Multi-line text input with label.

```python
from kokage_ui import DaisyTextarea

DaisyTextarea(label="Bio", name="bio", placeholder="Tell us about yourself", rows=5)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | str \| None | Label text |
| `name` | str | Textarea name attribute |
| `placeholder` | str | Placeholder text |
| `bordered` | bool | Bordered style (default: True) |
| `rows` | int | Number of rows (default: 3) |

## DaisyTable

Data table with headers and rows.

```python
from kokage_ui import DaisyTable

DaisyTable(
    headers=["Name", "Email", "Role"],
    rows=[
        ["Alice", "alice@example.com", "Admin"],
        ["Bob", "bob@example.com", "Editor"],
    ],
    zebra=True,
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `headers` | list[str] | Column header strings |
| `rows` | list[list] | List of rows (each row is a list of cell content) |
| `zebra` | bool | Zebra striping |
| `compact` | bool | Compact size (`table-xs`) |

## Toast

Notification toast that auto-dismisses.

```python
from kokage_ui import Toast

Toast("Saved successfully!", variant="success")
Toast("Error occurred", variant="error", position="toast-start toast-bottom")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | Any | Toast content |
| `variant` | str | `"info"`, `"success"`, `"warning"`, `"error"` |
| `position` | str | DaisyUI position classes (default: `"toast-end toast-top"`) |

## Layout

A reusable page layout builder (not a Component). Wraps content in a consistent `Page` with navbar, sidebar, footer, and theme.

```python
from kokage_ui import Layout, NavBar, A, Footer, P

layout = Layout(
    navbar=NavBar(start=A("My App", href="/", cls="btn btn-ghost text-xl")),
    footer=Footer(P("Footer content"), cls="p-4"),
    theme="light",
    title_suffix=" - My App",
    include_toast=True,
)
```

Use with `@ui.page()`:

```python
@ui.page("/", layout=layout, title="Home")
def home():
    return Div("Page content here")
```

Or with `ui.crud()`:

```python
ui.crud("/items", model=Item, storage=storage, layout=layout)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `navbar` | Any | NavBar or component for page top |
| `sidebar` | Any | Component for left sidebar |
| `footer` | Any | Component for page footer |
| `theme` | str | DaisyUI theme name (default: `"light"`) |
| `title_suffix` | str | Appended to every page title |
| `include_toast` | bool | Enable toast notifications |
| `include_sse` | bool | Load htmx SSE extension |
| `lang` | str | HTML lang attribute (default: `"ja"`) |
