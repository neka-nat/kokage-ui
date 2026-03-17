"""Build component catalog for MkDocs.

Generates Markdown pages with iframe-embedded previews for all kokage-ui components.

Usage:
    uv run python scripts/build_catalog.py
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from kokage_ui import (
    Accordion,
    Alert,
    AutoRefresh,
    Badge,
    Breadcrumb,
    Button,
    Card,
    Chart,
    CodeBlock,
    Collapse,
    ConfirmDelete,
    DaisyButton,
    DaisyInput,
    DaisySelect,
    DaisyTable,
    DaisyTextarea,
    DarkModeToggle,
    DateTimePicker,
    Details,
    Div,
    Dropdown,
    FileUpload,
    Form,
    H1,
    H2,
    H3,
    Hero,
    Img,
    InfiniteScroll,
    Input,
    Label,
    Li,
    LoginForm,
    Modal,
    ModelDetail,
    ModelForm,
    ModelTable,
    NavBar,
    Ol,
    Option,
    P,
    Progress,
    RegisterForm,
    RepeaterInput,
    RichTextEditor,
    SearchFilter,
    Select,
    SortableList,
    Span,
    Stat,
    Stats,
    Step,
    Steps,
)
from kokage_ui import Summary as Summary_
from kokage_ui import (
    Tab,
    Table,
    Tabs,
    TagInput,
    Tbody,
    Td,
    Th,
    Thead,
    ThemeSwitcher,
    Toast,
    Tr,
    Ul,
    Video,
)

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs" / "catalog"
PREVIEWS_DIR = DOCS_DIR / "previews"

PREVIEW_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <style>body {{ padding: 1rem; background: transparent; }}</style>
</head>
<body>
{body}
<script>
// Notify parent of content height for iframe auto-resize (with loop guard)
var _lastH = 0;
function notifyHeight() {{
  var h = document.body.scrollHeight;
  if (h !== _lastH) {{
    _lastH = h;
    window.parent.postMessage({{ type: "kokage-resize", height: h }}, "*");
  }}
}}
window.addEventListener("load", notifyHeight);
</script>
</body>
</html>
"""


@dataclass
class CatalogEntry:
    name: str
    category: str
    description: str
    code: str
    examples: list
    params: list[tuple[str, str, str]] | None = None


# ---------------------------------------------------------------------------
# Sample Pydantic models for ModelForm / ModelTable / ModelDetail previews
# ---------------------------------------------------------------------------

class SampleUser(BaseModel):
    name: str = Field(title="Name")
    email: str = Field(title="Email")
    age: int = Field(default=20, title="Age", ge=0, le=150)


class SampleTask(BaseModel):
    title: str = Field(title="Title")
    description: str = Field(default="", title="Description")
    done: bool = Field(default=False, title="Done")


# ---------------------------------------------------------------------------
# Catalog entries by category
# ---------------------------------------------------------------------------

def build_entries() -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []

    # ── elements ──────────────────────────────────────────────────────────
    entries.append(CatalogEntry(
        name="Button",
        category="elements",
        description="Standard HTML `<button>` element.",
        code='Button("Click me", type="submit")',
        examples=[Button("Click me", type="submit")],
        params=[
            ("*children", "Any", "Button content"),
            ("type", "str", "Button type (button/submit/reset)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Input",
        category="elements",
        description="HTML `<input>` element. Void element (no children).",
        code='Input(type="text", name="username", placeholder="Enter name")',
        examples=[Input(type="text", name="username", placeholder="Enter name")],
        params=[
            ("type", "str", "Input type (text/email/password/number/...)"),
            ("name", "str", "Field name"),
            ("placeholder", "str", "Placeholder text"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Select / Option",
        category="elements",
        description="HTML `<select>` with `<option>` children.",
        code=textwrap.dedent('''\
            Select(
                Option("Apple", value="apple"),
                Option("Banana", value="banana"),
                Option("Cherry", value="cherry"),
                name="fruit",
            )'''),
        examples=[Select(
            Option("Apple", value="apple"),
            Option("Banana", value="banana"),
            Option("Cherry", value="cherry"),
            name="fruit",
        )],
        params=[
            ("name", "str", "Field name"),
            ("*children", "Option", "Option elements"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Table",
        category="elements",
        description="HTML `<table>` with thead/tbody structure.",
        code=textwrap.dedent('''\
            Table(
                Thead(Tr(Th("Name"), Th("Age"))),
                Tbody(
                    Tr(Td("Alice"), Td("30")),
                    Tr(Td("Bob"), Td("25")),
                ),
            )'''),
        examples=[Table(
            Thead(Tr(Th("Name"), Th("Age"))),
            Tbody(
                Tr(Td("Alice"), Td("30")),
                Tr(Td("Bob"), Td("25")),
            ),
        )],
    ))

    entries.append(CatalogEntry(
        name="Form",
        category="elements",
        description="HTML `<form>` container.",
        code=textwrap.dedent('''\
            Form(
                Label("Name", Input(type="text", name="name")),
                Button("Submit", type="submit"),
                method="post",
            )'''),
        examples=[Form(
            Label("Name ", Input(type="text", name="name")),
            Button("Submit", type="submit"),
            method="post",
        )],
    ))

    entries.append(CatalogEntry(
        name="Ul / Ol",
        category="elements",
        description="Unordered and ordered list elements.",
        code=textwrap.dedent('''\
            Div(
                H3("Unordered"),
                Ul(Li("Item 1"), Li("Item 2"), Li("Item 3")),
                H3("Ordered"),
                Ol(Li("First"), Li("Second"), Li("Third")),
            )'''),
        examples=[Div(
            H3("Unordered"),
            Ul(Li("Item 1"), Li("Item 2"), Li("Item 3")),
            H3("Ordered"),
            Ol(Li("First"), Li("Second"), Li("Third")),
        )],
    ))

    entries.append(CatalogEntry(
        name="Details / Summary",
        category="elements",
        description="Disclosure widget with expandable content.",
        code=textwrap.dedent('''\
            Details(
                Summary("Click to expand"),
                P("Hidden content revealed on click."),
            )'''),
        examples=[Details(
            Summary_("Click to expand"),
            P("Hidden content revealed on click."),
        )],
    ))

    entries.append(CatalogEntry(
        name="Progress",
        category="elements",
        description="HTML `<progress>` bar.",
        code='Progress(value="70", max="100")',
        examples=[Progress(value="70", max="100")],
    ))

    entries.append(CatalogEntry(
        name="Video",
        category="elements",
        description="HTML `<video>` element.",
        code='Video(src="video.mp4", controls=True, width="320")',
        examples=[Video(controls=True, width="320", style="background:#eee;min-height:180px;")],
    ))

    entries.append(CatalogEntry(
        name="Img",
        category="elements",
        description="HTML `<img>` element.",
        code='Img(src="https://picsum.photos/300/200", alt="Sample")',
        examples=[Img(src="https://picsum.photos/300/200", alt="Sample image")],
    ))

    # ── components (DaisyUI) ─────────────────────────────────────────────
    entries.append(CatalogEntry(
        name="Card",
        category="components",
        description="A content container with optional title, image, and action buttons.",
        code=textwrap.dedent('''\
            Card(
                "Card content goes here.",
                title="Card Title",
                actions=[DaisyButton("Action", color="primary")],
            )'''),
        examples=[Card(
            "Card content goes here.",
            title="Card Title",
            actions=[DaisyButton("Action", color="primary")],
        )],
        params=[
            ("title", "str | None", "Card title text"),
            ("image", "str | None", "Image URL"),
            ("actions", "list[Any] | None", "Action buttons"),
            ("compact", "bool", "Compact size (card-sm)"),
            ("side", "bool", "Horizontal layout (lg:card-side)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Alert",
        category="components",
        description="Feedback message with variant styling.",
        code=textwrap.dedent('''\
            Div(
                Alert("Info message", variant="info"),
                Alert("Success!", variant="success"),
                Alert("Warning!", variant="warning"),
                Alert("Error!", variant="error"),
                cls="flex flex-col gap-2",
            )'''),
        examples=[Div(
            Alert("Info message", variant="info"),
            Alert("Success!", variant="success"),
            Alert("Warning!", variant="warning"),
            Alert("Error!", variant="error"),
            cls="flex flex-col gap-2",
        )],
        params=[
            ("variant", "str", '"info" | "success" | "warning" | "error"'),
        ],
    ))

    entries.append(CatalogEntry(
        name="Badge",
        category="components",
        description="Small label for status or category.",
        code=textwrap.dedent('''\
            Div(
                Badge("default"),
                Badge("primary", color="primary"),
                Badge("secondary", color="secondary"),
                Badge("accent", color="accent"),
                Badge("outline", color="primary", outline=True),
                cls="flex gap-2 flex-wrap",
            )'''),
        examples=[Div(
            Badge("default"),
            Badge("primary", color="primary"),
            Badge("secondary", color="secondary"),
            Badge("accent", color="accent"),
            Badge("outline", color="primary", outline=True),
            cls="flex gap-2 flex-wrap",
        )],
        params=[
            ("color", "str | None", "primary/secondary/accent/info/success/warning/error"),
            ("outline", "bool", "Outline style"),
            ("size", "str | None", '"xs" | "sm" | "md" | "lg"'),
        ],
    ))

    entries.append(CatalogEntry(
        name="DaisyButton",
        category="components",
        description="Styled button with color variants and sizes.",
        code=textwrap.dedent('''\
            Div(
                DaisyButton("Primary", color="primary"),
                DaisyButton("Secondary", color="secondary"),
                DaisyButton("Accent", color="accent"),
                DaisyButton("Outline", color="primary", variant="outline"),
                DaisyButton("Ghost", variant="ghost"),
                DaisyButton("Loading", color="primary", loading=True),
                cls="flex gap-2 flex-wrap",
            )'''),
        examples=[Div(
            DaisyButton("Primary", color="primary"),
            DaisyButton("Secondary", color="secondary"),
            DaisyButton("Accent", color="accent"),
            DaisyButton("Outline", color="primary", variant="outline"),
            DaisyButton("Ghost", variant="ghost"),
            DaisyButton("Loading", color="primary", loading=True),
            cls="flex gap-2 flex-wrap",
        )],
        params=[
            ("color", "str | None", "primary/secondary/accent/info/success/warning/error/neutral/ghost/link"),
            ("variant", "str | None", '"outline" | "ghost" | "soft" | "link"'),
            ("size", "str | None", '"xs" | "sm" | "md" | "lg"'),
            ("loading", "bool", "Show loading spinner"),
            ("disabled", "bool", "Disabled state"),
        ],
    ))

    entries.append(CatalogEntry(
        name="DaisyInput",
        category="components",
        description="Styled input field with label support.",
        code=textwrap.dedent('''\
            Div(
                DaisyInput(label="Username", name="username", placeholder="Enter username"),
                DaisyInput(label="Email", name="email", type="email", placeholder="you@example.com"),
                cls="flex flex-col gap-4 max-w-sm",
            )'''),
        examples=[Div(
            DaisyInput(label="Username", name="username", placeholder="Enter username"),
            DaisyInput(label="Email", name="email", type="email", placeholder="you@example.com"),
            cls="flex flex-col gap-4 max-w-sm",
        )],
        params=[
            ("label", "str | None", "Label text"),
            ("type", "str", "Input type (default: text)"),
            ("name", "str", "Field name"),
            ("placeholder", "str", "Placeholder text"),
            ("bordered", "bool", "Show border (default: True)"),
            ("required", "bool", "Required field"),
        ],
    ))

    entries.append(CatalogEntry(
        name="DaisySelect",
        category="components",
        description="Styled select dropdown with label.",
        code=textwrap.dedent('''\
            DaisySelect(
                options=[("apple", "Apple"), ("banana", "Banana"), ("cherry", "Cherry")],
                label="Favorite Fruit",
                name="fruit",
            )'''),
        examples=[DaisySelect(
            options=[("apple", "Apple"), ("banana", "Banana"), ("cherry", "Cherry")],
            label="Favorite Fruit",
            name="fruit",
        )],
        params=[
            ("options", 'list[tuple[str, str] | str]', "Choices as (value, label) or plain strings"),
            ("label", "str | None", "Label text"),
            ("name", "str", "Field name"),
            ("bordered", "bool", "Show border (default: True)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="DaisyTextarea",
        category="components",
        description="Styled textarea with label.",
        code=textwrap.dedent('''\
            DaisyTextarea(
                label="Message",
                name="message",
                placeholder="Type your message...",
                rows=4,
            )'''),
        examples=[DaisyTextarea(
            label="Message",
            name="message",
            placeholder="Type your message...",
            rows=4,
        )],
        params=[
            ("label", "str | None", "Label text"),
            ("name", "str", "Field name"),
            ("placeholder", "str", "Placeholder text"),
            ("rows", "int", "Number of rows (default: 3)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="DaisyTable",
        category="components",
        description="Styled table with headers and optional zebra striping.",
        code=textwrap.dedent('''\
            DaisyTable(
                headers=["Name", "Role", "Status"],
                rows=[
                    ["Alice", "Admin", "Active"],
                    ["Bob", "Editor", "Active"],
                    ["Charlie", "Viewer", "Inactive"],
                ],
                zebra=True,
            )'''),
        examples=[DaisyTable(
            headers=["Name", "Role", "Status"],
            rows=[
                ["Alice", "Admin", "Active"],
                ["Bob", "Editor", "Active"],
                ["Charlie", "Viewer", "Inactive"],
            ],
            zebra=True,
        )],
        params=[
            ("headers", "list[str]", "Column headers"),
            ("rows", "list[list[Any]]", "Table rows"),
            ("zebra", "bool", "Zebra striping"),
            ("compact", "bool", "Compact size"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Stats / Stat",
        category="components",
        description="Statistics display with title, value, and description.",
        code=textwrap.dedent('''\
            Stats(
                Stat(title="Total Users", value="31K", desc="+2.1% from last month"),
                Stat(title="Revenue", value="$4,200", desc="+12% from last month"),
                Stat(title="Active Now", value="573", desc="21 more than yesterday"),
            )'''),
        examples=[Stats(
            Stat(title="Total Users", value="31K", desc="+2.1% from last month"),
            Stat(title="Revenue", value="$4,200", desc="+12% from last month"),
            Stat(title="Active Now", value="573", desc="21 more than yesterday"),
        )],
        params=[
            ("title", "str", "Stat title"),
            ("value", "str", "Stat value"),
            ("desc", "str | None", "Description text"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Hero",
        category="components",
        description="Hero section with centered content.",
        code=textwrap.dedent('''\
            Hero(
                Div(
                    H1("Hello there", cls="text-5xl font-bold"),
                    P("Welcome to kokage-ui!", cls="py-6"),
                    DaisyButton("Get Started", color="primary"),
                    cls="hero-content text-center",
                ),
                min_height="20rem",
            )'''),
        examples=[Hero(
            Div(
                H1("Hello there", cls="text-5xl font-bold"),
                P("Welcome to kokage-ui!", cls="py-6"),
                DaisyButton("Get Started", color="primary"),
                cls="hero-content text-center",
            ),
            min_height="20rem",
        )],
        params=[
            ("min_height", "str | None", "CSS min-height"),
            ("overlay", "bool", "Add overlay"),
            ("image", "str | None", "Background image URL"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Modal",
        category="components",
        description="Dialog overlay triggered by a button.",
        code=textwrap.dedent('''\
            Div(
                DaisyButton("Open Modal", color="primary",
                             onclick="document.getElementById('demo-modal').showModal()"),
                Modal(
                    P("This is the modal content."),
                    modal_id="demo-modal",
                    title="Modal Title",
                    actions=[DaisyButton("Close", cls="btn")],
                ),
            )'''),
        examples=[Div(
            DaisyButton("Open Modal", color="primary",
                         onclick="document.getElementById('demo-modal').showModal()"),
            Modal(
                P("This is the modal content."),
                modal_id="demo-modal",
                title="Modal Title",
                actions=[DaisyButton("Close", cls="btn")],
            ),
        )],
        params=[
            ("modal_id", "str", "Required HTML id"),
            ("title", "str | None", "Modal title"),
            ("actions", "list[Any] | None", "Action buttons"),
            ("closable", "bool", "Close on backdrop click (default: True)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Tabs",
        category="components",
        description="Tabbed content navigation.",
        code=textwrap.dedent('''\
            Tabs(
                tabs=[
                    Tab(label="Tab 1", content=P("Content of tab 1"), active=True),
                    Tab(label="Tab 2", content=P("Content of tab 2")),
                    Tab(label="Tab 3", content=P("Content of tab 3")),
                ],
                variant="lifted",
            )'''),
        examples=[Tabs(
            tabs=[
                Tab(label="Tab 1", content=P("Content of tab 1"), active=True),
                Tab(label="Tab 2", content=P("Content of tab 2")),
                Tab(label="Tab 3", content=P("Content of tab 3")),
            ],
            variant="lifted",
        )],
        params=[
            ("tabs", "list[Tab]", "Tab definitions"),
            ("variant", "str | None", '"bordered" | "lifted" | "boxed"'),
            ("size", "str | None", '"xs" | "sm" | "md" | "lg"'),
        ],
    ))

    entries.append(CatalogEntry(
        name="Steps",
        category="components",
        description="Step indicator for multi-step processes.",
        code=textwrap.dedent('''\
            Steps(
                steps=[
                    Step(label="Register"),
                    Step(label="Choose plan"),
                    Step(label="Purchase"),
                    Step(label="Complete"),
                ],
                current=2,
                color="primary",
            )'''),
        examples=[Steps(
            steps=[
                Step(label="Register"),
                Step(label="Choose plan"),
                Step(label="Purchase"),
                Step(label="Complete"),
            ],
            current=2,
            color="primary",
        )],
        params=[
            ("steps", "list[Step]", "Step definitions"),
            ("current", "int", "Current step (0-indexed)"),
            ("color", "str", "Completed step color (default: primary)"),
            ("vertical", "bool", "Vertical layout"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Breadcrumb",
        category="components",
        description="Navigation breadcrumb trail.",
        code=textwrap.dedent('''\
            Breadcrumb(
                items=[
                    ("Home", "/"),
                    ("Documents", "/docs"),
                    ("Current Page", None),
                ],
            )'''),
        examples=[Breadcrumb(
            items=[
                ("Home", "/"),
                ("Documents", "/docs"),
                ("Current Page", None),
            ],
        )],
        params=[
            ("items", "list[tuple[str, str | None]]", "(label, href) pairs; None = current page"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Collapse / Accordion",
        category="components",
        description="Expandable content panels.",
        code=textwrap.dedent('''\
            Accordion(
                items=[
                    ("What is kokage-ui?", P("A Python library for building UIs with FastAPI.")),
                    ("How does it work?", P("It uses htmx and DaisyUI under the hood.")),
                    ("Is it free?", P("Yes, it is open source.")),
                ],
                variant="arrow",
                default_open=0,
            )'''),
        examples=[Accordion(
            items=[
                ("What is kokage-ui?", P("A Python library for building UIs with FastAPI.")),
                ("How does it work?", P("It uses htmx and DaisyUI under the hood.")),
                ("Is it free?", P("Yes, it is open source.")),
            ],
            variant="arrow",
            default_open=0,
        )],
        params=[
            ("items", "list[tuple[str, Any]]", "(title, content) pairs"),
            ("variant", "str | None", '"arrow" | "plus"'),
            ("default_open", "int | None", "Initially open panel (0-indexed)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Dropdown",
        category="components",
        description="Dropdown menu triggered by a button.",
        code=textwrap.dedent('''\
            Dropdown(
                "Menu",
                items=[
                    ("Profile", "/profile"),
                    ("Settings", "/settings"),
                    ("Logout", "/logout"),
                ],
            )'''),
        examples=[Dropdown(
            "Menu",
            items=[
                ("Profile", "#"),
                ("Settings", "#"),
                ("Logout", "#"),
            ],
        )],
        params=[
            ("trigger", "Any", "Trigger button text or component"),
            ("items", "list[tuple[str, str]] | None", "(label, href) pairs"),
            ("position", "str | None", '"top" | "bottom" | "left" | "right" | "end"'),
            ("hover", "bool", "Open on hover"),
        ],
    ))

    entries.append(CatalogEntry(
        name="FileUpload",
        category="components",
        description="Styled file upload input.",
        code=textwrap.dedent('''\
            FileUpload(
                name="avatar",
                label="Profile Picture",
                accept="image/*",
                color="primary",
            )'''),
        examples=[FileUpload(
            name="avatar",
            label="Profile Picture",
            accept="image/*",
            color="primary",
        )],
        params=[
            ("name", "str", "Input name"),
            ("label", "str | None", "Label text"),
            ("accept", "str | None", 'File types (e.g. "image/*")'),
            ("multiple", "bool", "Allow multiple files"),
            ("color", "str | None", "DaisyUI color"),
        ],
    ))

    entries.append(CatalogEntry(
        name="Toast",
        category="components",
        description="Notification toast positioned on screen.",
        code=textwrap.dedent('''\
            Toast(
                Alert("File saved successfully!", variant="success"),
                position="toast-end toast-top",
            )'''),
        examples=[Toast(
            Alert("File saved successfully!", variant="success"),
            position="toast-end toast-top",
        )],
        params=[
            ("variant", "str", '"info" | "success" | "warning" | "error"'),
            ("position", "str", "Position classes (default: toast-end toast-top)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="NavBar",
        category="components",
        description="Top navigation bar with start/center/end slots.",
        code=textwrap.dedent('''\
            NavBar(
                start=DaisyButton("kokage-ui", cls="btn btn-ghost text-xl"),
                center=Div(
                    DaisyButton("Home", variant="ghost"),
                    DaisyButton("Docs", variant="ghost"),
                ),
                end=DaisyButton("Login", color="primary", size="sm"),
            )'''),
        examples=[NavBar(
            start=DaisyButton("kokage-ui", cls="btn btn-ghost text-xl"),
            center=Div(
                DaisyButton("Home", variant="ghost"),
                DaisyButton("Docs", variant="ghost"),
            ),
            end=DaisyButton("Login", color="primary", size="sm"),
        )],
        params=[
            ("start", "Any", "Left slot content"),
            ("center", "Any", "Center slot content"),
            ("end", "Any", "Right slot content"),
        ],
    ))

    # ── fields ────────────────────────────────────────────────────────────
    entries.append(CatalogEntry(
        name="RichTextEditor",
        category="fields",
        description="Quill-based rich text editor (requires Quill JS).",
        code=textwrap.dedent('''\
            RichTextEditor(
                name="content",
                value="<p>Hello <strong>world</strong></p>",
                height="200px",
                placeholder="Write something...",
            )'''),
        examples=[RichTextEditor(
            name="content",
            value="<p>Hello <strong>world</strong></p>",
            height="200px",
            placeholder="Write something...",
        )],
        params=[
            ("name", "str", "Form field name"),
            ("value", "str", "Initial HTML content"),
            ("height", "str", 'Editor height (default: "300px")'),
            ("toolbar", "str", '"standard" | "minimal" | "full"'),
        ],
    ))

    entries.append(CatalogEntry(
        name="DateTimePicker",
        category="fields",
        description="Flatpickr-based date/time picker.",
        code=textwrap.dedent('''\
            DateTimePicker(
                name="event_date",
                value="2025-01-01",
            )'''),
        examples=[DateTimePicker(
            name="event_date",
            value="2025-01-01",
        )],
        params=[
            ("name", "str", "Form field name"),
            ("value", "str", "Initial value"),
            ("field_config", "DateField | TimeField | DateTimeField | None", "Field configuration"),
        ],
    ))

    entries.append(CatalogEntry(
        name="RepeaterInput",
        category="fields",
        description="Dynamic list of input fields with add/remove.",
        code=textwrap.dedent('''\
            RepeaterInput(
                name="tags",
                values=["Python", "FastAPI"],
                placeholder="Add tag...",
                add_label="+ Add Tag",
                max_items=5,
            )'''),
        examples=[RepeaterInput(
            name="tags",
            values=["Python", "FastAPI"],
            placeholder="Add tag...",
            add_label="+ Add Tag",
            max_items=5,
        )],
        params=[
            ("name", "str", "Form field name"),
            ("values", "list[str] | None", "Initial values"),
            ("min_items", "int", "Minimum rows"),
            ("max_items", "int | None", "Maximum rows"),
            ("placeholder", "str", "Input placeholder"),
            ("add_label", "str", 'Add button text (default: "Add")'),
        ],
    ))

    entries.append(CatalogEntry(
        name="TagInput",
        category="fields",
        description="Tag/chip input with keyboard support.",
        code=textwrap.dedent('''\
            TagInput(
                name="skills",
                values=["Python", "JavaScript", "Go"],
                placeholder="Add skill...",
                color="primary",
                max_tags=10,
            )'''),
        examples=[TagInput(
            name="skills",
            values=["Python", "JavaScript", "Go"],
            placeholder="Add skill...",
            color="primary",
            max_tags=10,
        )],
        params=[
            ("name", "str", "Form field name"),
            ("values", "list[str] | None", "Initial tags"),
            ("placeholder", "str", "Input placeholder"),
            ("max_tags", "int | None", "Maximum number of tags"),
            ("color", "str", "DaisyUI badge color (default: primary)"),
            ("separator", "str", 'Trigger character (default: ",")'),
        ],
    ))

    entries.append(CatalogEntry(
        name="SortableList",
        category="fields",
        description="Drag-and-drop sortable list (requires SortableJS).",
        code=textwrap.dedent('''\
            SortableList(
                items=[
                    {"id": "1", "label": "First item"},
                    {"id": "2", "label": "Second item"},
                    {"id": "3", "label": "Third item", "badge": "New"},
                ],
                url="/api/reorder",
            )'''),
        examples=[SortableList(
            items=[
                {"id": "1", "label": "First item"},
                {"id": "2", "label": "Second item"},
                {"id": "3", "label": "Third item", "badge": "New"},
            ],
            url="/api/reorder",
        )],
        params=[
            ("items", "list[dict]", 'Items with "id", "label", optional "badge"'),
            ("url", "str", "POST endpoint for reorder"),
            ("handle", "bool", "Show drag handle (default: True)"),
        ],
    ))

    # ── htmx ──────────────────────────────────────────────────────────────
    entries.append(CatalogEntry(
        name="SearchFilter",
        category="htmx",
        description="Live search input with debounced htmx requests.",
        code=textwrap.dedent('''\
            SearchFilter(
                url="/api/search",
                target="#results",
                placeholder="Search users...",
                delay=300,
            )'''),
        examples=[SearchFilter(
            url="/api/search",
            target="#results",
            placeholder="Search users...",
            delay=300,
        )],
        params=[
            ("url", "str", "Search endpoint"),
            ("target", "str", "Result target selector"),
            ("placeholder", "str", "Input placeholder"),
            ("delay", "int", "Debounce in ms (default: 300)"),
        ],
    ))

    entries.append(CatalogEntry(
        name="AutoRefresh",
        category="htmx",
        description="Periodically polls an endpoint to update content.",
        code=textwrap.dedent('''\
            AutoRefresh(
                P("Live data will appear here."),
                url="/api/status",
                interval=10,
            )'''),
        examples=[AutoRefresh(
            P("Live data will appear here."),
            url="/api/status",
            interval=10,
        )],
        params=[
            ("url", "str", "Poll endpoint"),
            ("interval", "int", "Seconds between polls (default: 5)"),
            ("target", "str | None", "Target selector"),
            ("swap", "str", 'Swap method (default: "innerHTML")'),
        ],
    ))

    entries.append(CatalogEntry(
        name="ConfirmDelete",
        category="htmx",
        description="Delete button with browser confirmation dialog.",
        code=textwrap.dedent('''\
            ConfirmDelete(
                "Delete Item",
                url="/api/items/1",
                confirm_message="Are you sure you want to delete this?",
                target="#item-1",
            )'''),
        examples=[ConfirmDelete(
            "Delete Item",
            url="/api/items/1",
            confirm_message="Are you sure you want to delete this?",
            target="#item-1",
        )],
        params=[
            ("url", "str", "DELETE endpoint"),
            ("confirm_message", "str", "Confirmation dialog text"),
            ("target", "str | None", "Target selector"),
            ("swap", "str", 'Swap method (default: "outerHTML")'),
        ],
    ))

    entries.append(CatalogEntry(
        name="InfiniteScroll",
        category="htmx",
        description="Load more content when scrolling to the bottom.",
        code=textwrap.dedent('''\
            InfiniteScroll(
                url="/api/items?page=2",
                target="#item-list",
                swap="beforeend",
            )'''),
        examples=[InfiniteScroll(
            url="/api/items?page=2",
            target="#item-list",
            swap="beforeend",
        )],
        params=[
            ("url", "str", "Next page endpoint"),
            ("target", "str | None", "Insert target"),
            ("swap", "str", 'Swap method (default: "beforeend")'),
            ("indicator", "Any", "Loading indicator"),
        ],
    ))

    # ── models ────────────────────────────────────────────────────────────
    entries.append(CatalogEntry(
        name="ModelForm",
        category="models",
        description="Auto-generated form from a Pydantic model.",
        code=textwrap.dedent('''\
            from pydantic import BaseModel, Field

            class User(BaseModel):
                name: str = Field(title="Name")
                email: str = Field(title="Email")
                age: int = Field(default=20, title="Age", ge=0, le=150)

            ModelForm(User, action="/users", submit_text="Create User")'''),
        examples=[ModelForm(SampleUser, action="/users", submit_text="Create User")],
        params=[
            ("model", "type[BaseModel]", "Pydantic model class"),
            ("action", "str", "Form action URL"),
            ("method", "str", 'HTTP method (default: "post")'),
            ("submit_text", "str", 'Submit button text (default: "Submit")'),
            ("exclude", "set[str] | None", "Fields to exclude"),
            ("instance", "BaseModel | None", "Pre-fill instance for editing"),
        ],
    ))

    entries.append(CatalogEntry(
        name="ModelTable",
        category="models",
        description="Auto-generated table from Pydantic model instances.",
        code=textwrap.dedent('''\
            ModelTable(
                User,
                rows=[
                    User(name="Alice", email="alice@example.com", age=30),
                    User(name="Bob", email="bob@example.com", age=25),
                ],
                zebra=True,
            )'''),
        examples=[ModelTable(
            SampleUser,
            rows=[
                SampleUser(name="Alice", email="alice@example.com", age=30),
                SampleUser(name="Bob", email="bob@example.com", age=25),
            ],
            zebra=True,
        )],
        params=[
            ("model", "type[BaseModel]", "Pydantic model class"),
            ("rows", "list[BaseModel]", "Data rows"),
            ("zebra", "bool", "Zebra striping"),
            ("compact", "bool", "Compact size"),
            ("exclude", "set[str] | None", "Fields to exclude"),
        ],
    ))

    entries.append(CatalogEntry(
        name="ModelDetail",
        category="models",
        description="Detail card showing a single model instance.",
        code=textwrap.dedent('''\
            ModelDetail(
                User(name="Alice", email="alice@example.com", age=30),
                title="User Profile",
            )'''),
        examples=[ModelDetail(
            SampleUser(name="Alice", email="alice@example.com", age=30),
            title="User Profile",
        )],
        params=[
            ("instance", "BaseModel", "Model instance to display"),
            ("title", "str | None", "Card title"),
            ("exclude", "set[str] | None", "Fields to exclude"),
        ],
    ))

    # ── features ──────────────────────────────────────────────────────────
    entries.append(CatalogEntry(
        name="LoginForm",
        category="features",
        description="Pre-built login form with username/password fields.",
        code=textwrap.dedent('''\
            LoginForm(
                action="/login",
                title="Sign In",
                register_url="/register",
                forgot_url="/forgot",
            )'''),
        examples=[LoginForm(
            action="/login",
            title="Sign In",
            register_url="/register",
            forgot_url="/forgot",
        )],
        params=[
            ("action", "str", 'Form action (default: "/login")'),
            ("title", "str", 'Form title (default: "Login")'),
            ("use_email", "bool", "Use email field instead of username"),
            ("register_url", "str | None", "Link to register page"),
            ("forgot_url", "str | None", "Link to forgot password page"),
        ],
    ))

    entries.append(CatalogEntry(
        name="RegisterForm",
        category="features",
        description="Pre-built registration form.",
        code=textwrap.dedent('''\
            RegisterForm(
                action="/register",
                title="Create Account",
                login_url="/login",
            )'''),
        examples=[RegisterForm(
            action="/register",
            title="Create Account",
            login_url="/login",
        )],
        params=[
            ("action", "str", 'Form action (default: "/register")'),
            ("title", "str", 'Form title (default: "Register")'),
            ("login_url", "str | None", "Link to login page"),
        ],
    ))

    entries.append(CatalogEntry(
        name="DarkModeToggle",
        category="features",
        description="Toggle button for light/dark theme switching.",
        code=textwrap.dedent('''\
            DarkModeToggle(
                light_theme="light",
                dark_theme="dark",
            )'''),
        examples=[DarkModeToggle(
            light_theme="light",
            dark_theme="dark",
        )],
        params=[
            ("light_theme", "str", 'Light theme name (default: "light")'),
            ("dark_theme", "str", 'Dark theme name (default: "dark")'),
            ("key", "str", "localStorage key"),
        ],
    ))

    entries.append(CatalogEntry(
        name="ThemeSwitcher",
        category="features",
        description="Dropdown for switching between multiple DaisyUI themes.",
        code=textwrap.dedent('''\
            ThemeSwitcher(
                themes=["light", "dark", "cupcake", "bumblebee", "emerald"],
                default="light",
            )'''),
        examples=[ThemeSwitcher(
            themes=["light", "dark", "cupcake", "bumblebee", "emerald"],
            default="light",
        )],
        params=[
            ("themes", "list[str]", "Available theme names"),
            ("default", "str", 'Default theme (default: "light")'),
        ],
    ))

    entries.append(CatalogEntry(
        name="Chart",
        category="features",
        description="Chart.js wrapper for line, bar, pie, and other charts.",
        code=textwrap.dedent('''\
            Chart(
                type="bar",
                data={
                    "labels": ["Jan", "Feb", "Mar", "Apr"],
                    "datasets": [{
                        "label": "Sales",
                        "data": [12, 19, 3, 5],
                    }],
                },
                height="300px",
            )'''),
        examples=[Chart(
            type="bar",
            data={
                "labels": ["Jan", "Feb", "Mar", "Apr"],
                "datasets": [{
                    "label": "Sales",
                    "data": [12, 19, 3, 5],
                }],
            },
            height="300px",
        )],
        params=[
            ("type", "str", '"line" | "bar" | "pie" | "doughnut" | "radar" | "scatter"'),
            ("data", "dict", "Chart.js data object"),
            ("options", "dict | None", "Chart.js options"),
            ("width", "str", 'CSS width (default: "100%")'),
            ("height", "str", 'CSS height (default: "400px")'),
        ],
    ))

    entries.append(CatalogEntry(
        name="CodeBlock",
        category="features",
        description="Syntax-highlighted code display (requires Highlight.js).",
        code=textwrap.dedent('''\
            CodeBlock(
                """def hello():
        print("Hello, world!")""",
                language="python",
                copy_button=True,
            )'''),
        examples=[CodeBlock(
            'def hello():\n    print("Hello, world!")',
            language="python",
            copy_button=True,
        )],
        params=[
            ("code", "str", "Source code to display"),
            ("language", "str | None", "Language for syntax highlighting"),
            ("copy_button", "bool", "Show copy button"),
        ],
    ))

    return entries


# ---------------------------------------------------------------------------
# Category metadata
# ---------------------------------------------------------------------------

CATEGORIES = {
    "elements": {
        "title": "HTML Elements",
        "description": "Low-level HTML element wrappers. These map directly to standard HTML tags with Python-friendly attribute naming (`cls` → `class`, `hx_get` → `hx-get`).",
    },
    "components": {
        "title": "DaisyUI Components",
        "description": "High-level UI components built on DaisyUI. These provide pre-styled, accessible widgets with Tailwind CSS classes.",
    },
    "fields": {
        "title": "Field Components",
        "description": "Specialized form field components for rich input experiences. Some require external JS libraries (Quill, flatpickr, SortableJS).",
    },
    "htmx": {
        "title": "htmx Patterns",
        "description": "Ready-made htmx interaction patterns. These generate the correct `hx-*` attributes for common dynamic UI patterns. Note: previews show the static HTML output only.",
    },
    "models": {
        "title": "Model Components",
        "description": "Auto-generated UI from Pydantic models. These inspect model fields to create forms, tables, and detail views automatically.",
    },
    "features": {
        "title": "Features",
        "description": "Higher-level feature components for authentication, theming, charting, and code display.",
    },
}


def render_component(component) -> str:
    """Render a component to HTML string."""
    return str(component.render()) if hasattr(component, "render") else str(component)


def generate_preview_html(entry: CatalogEntry) -> str:
    """Generate standalone preview HTML for iframe embedding."""
    parts = []
    for example in entry.examples:
        parts.append(render_component(example))
    body = "\n".join(parts)
    return PREVIEW_HTML_TEMPLATE.format(body=body)


def preview_filename(entry: CatalogEntry) -> str:
    """Generate a filename for the preview HTML."""
    return entry.name.lower().replace(" / ", "-").replace(" ", "-") + ".html"


def generate_category_page(category: str, entries: list[CatalogEntry]) -> str:
    """Generate a Markdown page for a category."""
    meta = CATEGORIES[category]
    lines = [
        f"# {meta['title']}",
        "",
        meta["description"],
        "",
    ]

    for entry in entries:
        fname = preview_filename(entry)
        lines.append(f"## {entry.name}")
        lines.append("")
        lines.append(entry.description)
        lines.append("")
        lines.append("### Preview")
        lines.append("")
        lines.append(
            f'<iframe src="../previews/{fname}" '
            f'style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" '
            f'loading="lazy"></iframe>'
        )
        lines.append("")
        lines.append("### Code")
        lines.append("")
        lines.append("```python")
        lines.append(entry.code)
        lines.append("```")
        lines.append("")

        if entry.params:
            lines.append("### Parameters")
            lines.append("")
            lines.append("| Parameter | Type | Description |")
            lines.append("|-----------|------|-------------|")
            for pname, ptype, pdesc in entry.params:
                lines.append(f"| `{pname}` | `{ptype}` | {pdesc} |")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def generate_index_page() -> str:
    """Generate the catalog index page."""
    lines = [
        "# Component Catalog",
        "",
        "Browse all kokage-ui components with live previews.",
        "",
    ]

    for cat_key, cat_meta in CATEGORIES.items():
        lines.append(f"## [{cat_meta['title']}]({cat_key}.md)")
        lines.append("")
        lines.append(cat_meta["description"])
        lines.append("")

    return "\n".join(lines)


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    entries = build_entries()

    # Group by category
    by_category: dict[str, list[CatalogEntry]] = {}
    for entry in entries:
        by_category.setdefault(entry.category, []).append(entry)

    # Generate preview HTML files
    preview_count = 0
    for entry in entries:
        html = generate_preview_html(entry)
        path = PREVIEWS_DIR / preview_filename(entry)
        path.write_text(html, encoding="utf-8")
        preview_count += 1

    # Generate category pages
    for category, cat_entries in by_category.items():
        md = generate_category_page(category, cat_entries)
        path = DOCS_DIR / f"{category}.md"
        path.write_text(md, encoding="utf-8")

    # Generate index page
    index_md = generate_index_page()
    (DOCS_DIR / "index.md").write_text(index_md, encoding="utf-8")

    print(f"Catalog generated: {len(entries)} components, {preview_count} previews")
    print(f"Output: {DOCS_DIR}")


if __name__ == "__main__":
    main()
