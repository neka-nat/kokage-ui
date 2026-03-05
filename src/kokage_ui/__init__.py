"""kokage - Add htmx + DaisyUI based UI to FastAPI with pure Python.

Example:
    from fastapi import FastAPI
    from kokage_ui import KokageUI, Page, Div, H1, Card, DaisyButton

    app = FastAPI()
    ui = KokageUI(app)

    @ui.page("/")
    def index():
        return Page(
            Card(H1("Hello, kokage!"), title="Welcome"),
            title="My App",
        )
"""

__version__ = "0.2.0"

# FastAPI integration
from kokage_ui.core import KokageUI

# Page layout
from kokage_ui.page import Page

# Base HTML elements
from kokage_ui.elements import (
    A,
    Article,
    Aside,
    Blockquote,
    Body,
    Br,
    Button,
    Code,
    Component,
    Details,
    Dialog,
    Div,
    Em,
    Fieldset,
    Figcaption,
    Figure,
    Footer,
    Form,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    Head,
    Header,
    Hr,
    Html,
    Img,
    Input,
    Label,
    Legend,
    Li,
    Link,
    Main,
    Meta,
    Nav,
    Ol,
    Option,
    P,
    Pre,
    Progress,
    Raw,
    Script,
    Section,
    Select,
    Small,
    Span,
    Strong,
    Style,
    Summary,
    Table,
    Tbody,
    Td,
    Textarea,
    Tfoot,
    Th,
    Thead,
    Title,
    Tr,
    Ul,
)

# DaisyUI components
from kokage_ui.components import (
    Accordion,
    Alert,
    Badge,
    Breadcrumb,
    Card,
    Collapse,
    DaisyButton,
    DaisyInput,
    DaisySelect,
    DaisyTable,
    DaisyTextarea,
    Drawer,
    Dropdown,
    Hero,
    Layout,
    Modal,
    NavBar,
    Stat,
    Stats,
    Step,
    Steps,
    Tab,
    Tabs,
    Toast,
)

# Pydantic model → UI auto-generation
from kokage_ui.models import ModelDetail, ModelForm, ModelTable

# htmx helpers
from kokage_ui.htmx import (
    AutoRefresh,
    ConfirmDelete,
    HxSwapOOB,
    InfiniteScroll,
    SSEStream,
    SearchFilter,
)

# CRUD auto-generation
from kokage_ui.crud import CRUDRouter, InMemoryStorage, Pagination, Storage

__all__ = [
    # Core
    "KokageUI",
    "Page",
    "Component",
    "Raw",
    # HTML Elements
    "Div",
    "Span",
    "Section",
    "Article",
    "Aside",
    "Header",
    "Footer",
    "Main",
    "Nav",
    "P",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "Strong",
    "Em",
    "Small",
    "Pre",
    "Code",
    "Blockquote",
    "A",
    "Img",
    "Br",
    "Hr",
    "Ul",
    "Ol",
    "Li",
    "Table",
    "Thead",
    "Tbody",
    "Tfoot",
    "Tr",
    "Th",
    "Td",
    "Form",
    "Button",
    "Input",
    "Textarea",
    "Select",
    "Option",
    "Label",
    "Fieldset",
    "Legend",
    "Script",
    "Style",
    "Link",
    "Meta",
    "Title",
    "Head",
    "Body",
    "Html",
    "Figure",
    "Figcaption",
    "Details",
    "Summary",
    "Dialog",
    "Progress",
    # DaisyUI Components
    "Card",
    "Stat",
    "Stats",
    "Hero",
    "Alert",
    "Badge",
    "NavBar",
    "DaisyButton",
    "DaisyInput",
    "DaisySelect",
    "DaisyTextarea",
    "DaisyTable",
    "Toast",
    "Layout",
    "Modal",
    "Drawer",
    "Tab",
    "Tabs",
    "Step",
    "Steps",
    "Breadcrumb",
    "Collapse",
    "Accordion",
    "Dropdown",
    # Pydantic Model → UI
    "ModelForm",
    "ModelTable",
    "ModelDetail",
    # htmx Helpers
    "HxSwapOOB",
    "AutoRefresh",
    "SearchFilter",
    "InfiniteScroll",
    "SSEStream",
    "ConfirmDelete",
    # CRUD
    "CRUDRouter",
    "Storage",
    "InMemoryStorage",
    "Pagination",
]
