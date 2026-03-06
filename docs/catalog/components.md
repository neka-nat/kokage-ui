# DaisyUI Components

High-level UI components built on DaisyUI. These provide pre-styled, accessible widgets with Tailwind CSS classes.

## Card

A content container with optional title, image, and action buttons.

### Preview

<iframe src="../previews/card.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Card(
    "Card content goes here.",
    title="Card Title",
    actions=[DaisyButton("Action", color="primary")],
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | `str | None` | Card title text |
| `image` | `str | None` | Image URL |
| `actions` | `list[Any] | None` | Action buttons |
| `compact` | `bool` | Compact size (card-sm) |
| `side` | `bool` | Horizontal layout (lg:card-side) |

---

## Alert

Feedback message with variant styling.

### Preview

<iframe src="../previews/alert.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Div(
    Alert("Info message", variant="info"),
    Alert("Success!", variant="success"),
    Alert("Warning!", variant="warning"),
    Alert("Error!", variant="error"),
    cls="flex flex-col gap-2",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `variant` | `str` | "info" | "success" | "warning" | "error" |

---

## Badge

Small label for status or category.

### Preview

<iframe src="../previews/badge.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Div(
    Badge("default"),
    Badge("primary", color="primary"),
    Badge("secondary", color="secondary"),
    Badge("accent", color="accent"),
    Badge("outline", color="primary", outline=True),
    cls="flex gap-2 flex-wrap",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `color` | `str | None` | primary/secondary/accent/info/success/warning/error |
| `outline` | `bool` | Outline style |
| `size` | `str | None` | "xs" | "sm" | "md" | "lg" |

---

## DaisyButton

Styled button with color variants and sizes.

### Preview

<iframe src="../previews/daisybutton.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Div(
    DaisyButton("Primary", color="primary"),
    DaisyButton("Secondary", color="secondary"),
    DaisyButton("Accent", color="accent"),
    DaisyButton("Outline", color="primary", variant="outline"),
    DaisyButton("Ghost", variant="ghost"),
    DaisyButton("Loading", color="primary", loading=True),
    cls="flex gap-2 flex-wrap",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `color` | `str | None` | primary/secondary/accent/info/success/warning/error/neutral/ghost/link |
| `variant` | `str | None` | "outline" | "ghost" | "soft" | "link" |
| `size` | `str | None` | "xs" | "sm" | "md" | "lg" |
| `loading` | `bool` | Show loading spinner |
| `disabled` | `bool` | Disabled state |

---

## DaisyInput

Styled input field with label support.

### Preview

<iframe src="../previews/daisyinput.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Div(
    DaisyInput(label="Username", name="username", placeholder="Enter username"),
    DaisyInput(label="Email", name="email", type="email", placeholder="you@example.com"),
    cls="flex flex-col gap-4 max-w-sm",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | `str | None` | Label text |
| `type` | `str` | Input type (default: text) |
| `name` | `str` | Field name |
| `placeholder` | `str` | Placeholder text |
| `bordered` | `bool` | Show border (default: True) |
| `required` | `bool` | Required field |

---

## DaisySelect

Styled select dropdown with label.

### Preview

<iframe src="../previews/daisyselect.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
DaisySelect(
    options=[("apple", "Apple"), ("banana", "Banana"), ("cherry", "Cherry")],
    label="Favorite Fruit",
    name="fruit",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `options` | `list[tuple[str, str] | str]` | Choices as (value, label) or plain strings |
| `label` | `str | None` | Label text |
| `name` | `str` | Field name |
| `bordered` | `bool` | Show border (default: True) |

---

## DaisyTextarea

Styled textarea with label.

### Preview

<iframe src="../previews/daisytextarea.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
DaisyTextarea(
    label="Message",
    name="message",
    placeholder="Type your message...",
    rows=4,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | `str | None` | Label text |
| `name` | `str` | Field name |
| `placeholder` | `str` | Placeholder text |
| `rows` | `int` | Number of rows (default: 3) |

---

## DaisyTable

Styled table with headers and optional zebra striping.

### Preview

<iframe src="../previews/daisytable.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
DaisyTable(
    headers=["Name", "Role", "Status"],
    rows=[
        ["Alice", "Admin", "Active"],
        ["Bob", "Editor", "Active"],
        ["Charlie", "Viewer", "Inactive"],
    ],
    zebra=True,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `headers` | `list[str]` | Column headers |
| `rows` | `list[list[Any]]` | Table rows |
| `zebra` | `bool` | Zebra striping |
| `compact` | `bool` | Compact size |

---

## Stats / Stat

Statistics display with title, value, and description.

### Preview

<iframe src="../previews/stats-stat.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Stats(
    Stat(title="Total Users", value="31K", desc="+2.1% from last month"),
    Stat(title="Revenue", value="$4,200", desc="+12% from last month"),
    Stat(title="Active Now", value="573", desc="21 more than yesterday"),
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | `str` | Stat title |
| `value` | `str` | Stat value |
| `desc` | `str | None` | Description text |

---

## Hero

Hero section with centered content.

### Preview

<iframe src="../previews/hero.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Hero(
    Div(
        H1("Hello there", cls="text-5xl font-bold"),
        P("Welcome to kokage-ui!", cls="py-6"),
        DaisyButton("Get Started", color="primary"),
        cls="hero-content text-center",
    ),
    min_height="20rem",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_height` | `str | None` | CSS min-height |
| `overlay` | `bool` | Add overlay |
| `image` | `str | None` | Background image URL |

---

## Modal

Dialog overlay triggered by a button.

### Preview

<iframe src="../previews/modal.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Div(
    DaisyButton("Open Modal", color="primary",
                 onclick="document.getElementById('demo-modal').showModal()"),
    Modal(
        P("This is the modal content."),
        modal_id="demo-modal",
        title="Modal Title",
        actions=[DaisyButton("Close", cls="btn")],
    ),
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `modal_id` | `str` | Required HTML id |
| `title` | `str | None` | Modal title |
| `actions` | `list[Any] | None` | Action buttons |
| `closable` | `bool` | Close on backdrop click (default: True) |

---

## Tabs

Tabbed content navigation.

### Preview

<iframe src="../previews/tabs.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Tabs(
    tabs=[
        Tab(label="Tab 1", content=P("Content of tab 1"), active=True),
        Tab(label="Tab 2", content=P("Content of tab 2")),
        Tab(label="Tab 3", content=P("Content of tab 3")),
    ],
    variant="lifted",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `tabs` | `list[Tab]` | Tab definitions |
| `variant` | `str | None` | "bordered" | "lifted" | "boxed" |
| `size` | `str | None` | "xs" | "sm" | "md" | "lg" |

---

## Steps

Step indicator for multi-step processes.

### Preview

<iframe src="../previews/steps.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Steps(
    steps=[
        Step(label="Register"),
        Step(label="Choose plan"),
        Step(label="Purchase"),
        Step(label="Complete"),
    ],
    current=2,
    color="primary",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `steps` | `list[Step]` | Step definitions |
| `current` | `int` | Current step (0-indexed) |
| `color` | `str` | Completed step color (default: primary) |
| `vertical` | `bool` | Vertical layout |

---

## Breadcrumb

Navigation breadcrumb trail.

### Preview

<iframe src="../previews/breadcrumb.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Breadcrumb(
    items=[
        ("Home", "/"),
        ("Documents", "/docs"),
        ("Current Page", None),
    ],
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `items` | `list[tuple[str, str | None]]` | (label, href) pairs; None = current page |

---

## Collapse / Accordion

Expandable content panels.

### Preview

<iframe src="../previews/collapse-accordion.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Accordion(
    items=[
        ("What is kokage-ui?", P("A Python library for building UIs with FastAPI.")),
        ("How does it work?", P("It uses htmx and DaisyUI under the hood.")),
        ("Is it free?", P("Yes, it is open source.")),
    ],
    variant="arrow",
    default_open=0,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `items` | `list[tuple[str, Any]]` | (title, content) pairs |
| `variant` | `str | None` | "arrow" | "plus" |
| `default_open` | `int | None` | Initially open panel (0-indexed) |

---

## Dropdown

Dropdown menu triggered by a button.

### Preview

<iframe src="../previews/dropdown.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Dropdown(
    "Menu",
    items=[
        ("Profile", "/profile"),
        ("Settings", "/settings"),
        ("Logout", "/logout"),
    ],
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `trigger` | `Any` | Trigger button text or component |
| `items` | `list[tuple[str, str]] | None` | (label, href) pairs |
| `position` | `str | None` | "top" | "bottom" | "left" | "right" | "end" |
| `hover` | `bool` | Open on hover |

---

## FileUpload

Styled file upload input.

### Preview

<iframe src="../previews/fileupload.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
FileUpload(
    name="avatar",
    label="Profile Picture",
    accept="image/*",
    color="primary",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Input name |
| `label` | `str | None` | Label text |
| `accept` | `str | None` | File types (e.g. "image/*") |
| `multiple` | `bool` | Allow multiple files |
| `color` | `str | None` | DaisyUI color |

---

## Toast

Notification toast positioned on screen.

### Preview

<iframe src="../previews/toast.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Toast(
    Alert("File saved successfully!", variant="success"),
    position="toast-end toast-top",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `variant` | `str` | "info" | "success" | "warning" | "error" |
| `position` | `str` | Position classes (default: toast-end toast-top) |

---

## NavBar

Top navigation bar with start/center/end slots.

### Preview

<iframe src="../previews/navbar.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
NavBar(
    start=DaisyButton("kokage-ui", cls="btn btn-ghost text-xl"),
    center=Div(
        DaisyButton("Home", variant="ghost"),
        DaisyButton("Docs", variant="ghost"),
    ),
    end=DaisyButton("Login", color="primary", size="sm"),
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start` | `Any` | Left slot content |
| `center` | `Any` | Center slot content |
| `end` | `Any` | Right slot content |

---
