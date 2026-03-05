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
    Audio,
    Canvas,
    Picture,
    Progress,
    Raw,
    Source,
    Track,
    Video,
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
    DependentSelect,
    Drawer,
    Dropdown,
    DropZone,
    FileUpload,
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
from kokage_ui.models import ModelDetail, ModelForm, ModelTable, SortableTable, ValidatedModelForm

# Data display
from kokage_ui.charts import Chart
from kokage_ui.code import CodeBlock
from kokage_ui.markdown import Markdown

# htmx helpers
from kokage_ui.htmx import (
    AutoRefresh,
    ConfirmDelete,
    DependentField,
    HxSwapOOB,
    InfiniteScroll,
    SSEStream,
    SearchFilter,
)

# Multi-step forms
from kokage_ui.forms import FormStep, MultiStepForm

# Authentication & authorization
from kokage_ui.auth import LoginForm, RegisterForm, RoleGuard, UserMenu, protected

# Theme switching
from kokage_ui.theme import DarkModeToggle, ThemeSwitcher

# Notifications
from kokage_ui.notifications import Notifier, NotificationStream

# DataGrid
from kokage_ui.datagrid import ColumnFilter, DataGrid, DataGridState

# CRUD auto-generation
from kokage_ui.crud import CRUDRouter, InMemoryStorage, Pagination, Storage
from kokage_ui.storage import SQLModelStorage, create_tables

# Sortable
from kokage_ui.sortable import SortableList

# Media
from kokage_ui.media import AudioPlayer, ImageGallery, MediaCard, MediaField, VideoPlayer

# Rich Text
from kokage_ui.richtext import RichTextEditor, RichTextField

# Repeater
from kokage_ui.repeater import RepeaterField, RepeaterInput

# Admin dashboard
from kokage_ui.admin import AdminSite, ModelAdmin

# Testing helpers
from kokage_ui.testing import (
    HTMLAssertions,
    ResponseAssertions,
    assert_response,
    make_app,
    make_client,
    render,
    rendered,
)

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
    "Video",
    "Audio",
    "Picture",
    "Canvas",
    "Source",
    "Track",
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
    "ValidatedModelForm",
    "ModelTable",
    "ModelDetail",
    # htmx Helpers
    "HxSwapOOB",
    "AutoRefresh",
    "SearchFilter",
    "InfiniteScroll",
    "SSEStream",
    "ConfirmDelete",
    "DependentField",
    # Components (new)
    "FileUpload",
    "DropZone",
    "DependentSelect",
    # Multi-step Forms
    "FormStep",
    "MultiStepForm",
    # CRUD
    "CRUDRouter",
    "Storage",
    "InMemoryStorage",
    "Pagination",
    "SQLModelStorage",
    "create_tables",
    # Data Display
    "Chart",
    "Markdown",
    "CodeBlock",
    "SortableTable",
    # DataGrid
    "DataGrid",
    "DataGridState",
    "ColumnFilter",
    # Theme
    "DarkModeToggle",
    "ThemeSwitcher",
    # Auth
    "LoginForm",
    "RegisterForm",
    "UserMenu",
    "RoleGuard",
    "protected",
    # Admin
    "AdminSite",
    "ModelAdmin",
    # Notifications
    "Notifier",
    "NotificationStream",
    # Sortable
    "SortableList",
    # Media
    "MediaField",
    "VideoPlayer",
    "AudioPlayer",
    "ImageGallery",
    "MediaCard",
    # Rich Text
    "RichTextEditor",
    "RichTextField",
    # Repeater
    "RepeaterField",
    "RepeaterInput",
    # Testing
    "render",
    "rendered",
    "HTMLAssertions",
    "ResponseAssertions",
    "assert_response",
    "make_app",
    "make_client",
]
