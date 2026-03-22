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
    Autocomplete,
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
    Timeline,
    TimelineItem,
    Tabs,
    Toast,
    autocomplete_option,
)

# Pydantic model → UI auto-generation
from kokage_ui.models import ModelDetail, ModelForm, ModelTable, SortableTable, ValidatedModelForm

# Data display
from kokage_ui.features.charts import Chart, ChartData, ChartOptions, Dataset
from kokage_ui.features.code import CodeBlock
from kokage_ui.features.markdown import Markdown

# htmx helpers
from kokage_ui.htmx import (
    AutoRefresh,
    ConfirmDelete,
    DependentField,
    HxSwapOOB,
    InfiniteScroll,
    InlineEdit,
    SSEStream,
    SearchFilter,
)

# Multi-step forms
from kokage_ui.features.forms import FormStep, MultiStepForm

# Authentication & authorization
from kokage_ui.features.auth import LoginForm, RegisterForm, RoleGuard, UserMenu, protected

# Theme switching
from kokage_ui.features.theme import DarkModeToggle, ThemeSwitcher

# Notifications
from kokage_ui.features.notifications import Notifier, NotificationStream

# DataGrid
from kokage_ui.data.datagrid import ColumnFilter, DataGrid, DataGridState

# CRUD auto-generation
from kokage_ui.data.crud import CRUDRouter, InMemoryStorage, Pagination, Storage
from kokage_ui.data.storage import SQLModelStorage, create_tables

# Sortable
from kokage_ui.fields.sortable import SortableList

# Media
from kokage_ui.fields.media import AudioPlayer, ImageGallery, MediaCard, MediaField, VideoPlayer

# Rich Text
from kokage_ui.fields.richtext import RichTextEditor, RichTextField

# Repeater
from kokage_ui.fields.repeater import RepeaterField, RepeaterInput

# Tag
from kokage_ui.fields.tag import TagField, TagInput

# DateTime
from kokage_ui.fields.datetime import DateField, DateTimeField, DateTimePicker, TimeField

# i18n
from kokage_ui.features.i18n import (
    LanguageSwitcher,
    LocaleMiddleware,
    add_locale,
    configure as configure_i18n,
    get_locale,
    set_locale,
    t,
)

# AI chat
from kokage_ui.ai import ChatMessage, ChatView, chat_stream

# AI agent
from kokage_ui.ai import AgentEvent, AgentMessage, AgentView, ToolCall, agent_stream

# AI tools
from kokage_ui.ai import ToolInfo, ToolRegistry

# AI conversation
from kokage_ui.ai import ConversationStore, InMemoryConversationStore, Message, Thread

# AI preview
from kokage_ui.ai import FilePreview

# Admin dashboard
from kokage_ui.features.admin import ActivityEntry, ActivityLog, AdminSite, ModelAdmin

# Testing helpers
from kokage_ui.dev.testing import (
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
    "Timeline",
    "TimelineItem",
    "Breadcrumb",
    "Collapse",
    "Accordion",
    "Dropdown",
    "Autocomplete",
    "autocomplete_option",
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
    "InlineEdit",
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
    "ChartData",
    "ChartOptions",
    "Dataset",
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
    # i18n
    "t",
    "configure_i18n",
    "add_locale",
    "get_locale",
    "set_locale",
    "LocaleMiddleware",
    "LanguageSwitcher",
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
    # Tag
    "TagField",
    "TagInput",
    # DateTime
    "DateField",
    "TimeField",
    "DateTimeField",
    "DateTimePicker",
    # AI
    "ChatMessage",
    "ChatView",
    "chat_stream",
    "AgentEvent",
    "AgentMessage",
    "AgentView",
    "ToolCall",
    "ToolInfo",
    "ToolRegistry",
    "agent_stream",
    "ConversationStore",
    "InMemoryConversationStore",
    "Message",
    "Thread",
    "FilePreview",
    # Testing
    "render",
    "rendered",
    "HTMLAssertions",
    "ResponseAssertions",
    "assert_response",
    "make_app",
    "make_client",
]
