# API Reference

Quick reference of all exports from `kokage_ui`.

## Core

| Export | Module | Description |
|--------|--------|-------------|
| `KokageUI` | `core` | FastAPI integration — `page()`, `fragment()`, `crud()`, `validate()` decorators |
| `Page` | `page` | Full `<!DOCTYPE html>` document generator |

## HTML Elements

All elements inherit from `Component`. Children are positional args, attributes are keyword args.

| Export | Tag | Notes |
|--------|-----|-------|
| `Component` | `div` | Base class for all elements |
| `Raw` | — | Insert raw (unescaped) HTML |
| `Div` | `<div>` | |
| `Span` | `<span>` | |
| `Section` | `<section>` | |
| `Article` | `<article>` | |
| `Aside` | `<aside>` | |
| `Header` | `<header>` | |
| `Footer` | `<footer>` | |
| `Main` | `<main>` | |
| `Nav` | `<nav>` | |
| `P` | `<p>` | |
| `H1` – `H6` | `<h1>` – `<h6>` | |
| `Strong` | `<strong>` | |
| `Em` | `<em>` | |
| `Small` | `<small>` | |
| `Pre` | `<pre>` | |
| `Code` | `<code>` | |
| `Blockquote` | `<blockquote>` | |
| `A` | `<a>` | |
| `Img` | `<img>` | Void element |
| `Br` | `<br>` | Void element |
| `Hr` | `<hr>` | Void element |
| `Ul` | `<ul>` | |
| `Ol` | `<ol>` | |
| `Li` | `<li>` | |
| `Table` | `<table>` | |
| `Thead` | `<thead>` | |
| `Tbody` | `<tbody>` | |
| `Tfoot` | `<tfoot>` | |
| `Tr` | `<tr>` | |
| `Th` | `<th>` | |
| `Td` | `<td>` | |
| `Form` | `<form>` | |
| `Button` | `<button>` | |
| `Input` | `<input>` | Void element |
| `Textarea` | `<textarea>` | |
| `Select` | `<select>` | |
| `Option` | `<option>` | |
| `Label` | `<label>` | |
| `Fieldset` | `<fieldset>` | |
| `Legend` | `<legend>` | |
| `Script` | `<script>` | |
| `Style` | `<style>` | |
| `Link` | `<link>` | Void element |
| `Meta` | `<meta>` | Void element |
| `Title` | `<title>` | |
| `Head` | `<head>` | |
| `Body` | `<body>` | |
| `Html` | `<html>` | |
| `Figure` | `<figure>` | |
| `Figcaption` | `<figcaption>` | |
| `Details` | `<details>` | |
| `Summary` | `<summary>` | |
| `Dialog` | `<dialog>` | |
| `Progress` | `<progress>` | |

## DaisyUI Components

| Export | Description |
|--------|-------------|
| `Card` | Card with title, image, actions |
| `Stat` | Single stat item |
| `Stats` | Stats container |
| `Hero` | Hero banner section |
| `Alert` | Alert notification (info/success/warning/error) |
| `Badge` | Small label badge |
| `NavBar` | Navigation bar (start/center/end) |
| `DaisyButton` | Styled button (color/variant/size) |
| `DaisyInput` | Form input with label |
| `DaisySelect` | Select dropdown with label |
| `DaisyTextarea` | Textarea with label |
| `DaisyTable` | Data table with headers and rows |
| `Toast` | Toast notification |
| `Layout` | Reusable page layout builder |
| `Modal` | Dialog overlay (`showModal()`) |
| `Drawer` | Sidebar/off-canvas panel |
| `Tab` | Single tab definition (dataclass) |
| `Tabs` | Tabbed navigation (link or content mode) |
| `Step` | Single step definition (dataclass) |
| `Steps` | Progress step indicator |
| `Breadcrumb` | Navigation breadcrumb trail |
| `Collapse` | Expandable content section |
| `Accordion` | Radio-linked collapse group |
| `Dropdown` | Dropdown menu (click or hover) |
| `FileUpload` | File upload input with styling |
| `DropZone` | Drag-and-drop file upload area |
| `DependentSelect` | Select that depends on another field |

## Pydantic Model → UI

| Export | Description |
|--------|-------------|
| `ModelForm` | Auto-generate form from BaseModel |
| `ValidatedModelForm` | Form with real-time field validation |
| `ModelTable` | Auto-generate table from BaseModel + rows |
| `ModelDetail` | Auto-generate detail card from model instance |
| `SortableTable` | Table with sortable column headers |

## DataGrid

| Export | Description |
|--------|-------------|
| `DataGrid` | Advanced table with sort, filter, pagination, bulk actions, CSV export |
| `DataGridState` | Parse grid state from request query parameters |
| `ColumnFilter` | Per-column filter definition (text, select, number_range) |

## htmx Helpers

| Export | Description |
|--------|-------------|
| `AutoRefresh` | Poll URL at interval (`hx-trigger="every Ns"`) |
| `SearchFilter` | Debounced search input (`hx-trigger="keyup changed delay:Nms"`) |
| `InfiniteScroll` | Load on scroll (`hx-trigger="revealed"`) |
| `SSEStream` | Server-Sent Events receiver (htmx SSE extension) |
| `ConfirmDelete` | Delete button with confirmation (`hx-confirm` + `hx-delete`) |
| `HxSwapOOB` | Out-of-Band swap (`hx-swap-oob`) |
| `DependentField` | Field that updates based on another field's value |

## Multi-step Forms

| Export | Description |
|--------|-------------|
| `FormStep` | Step definition (title, fields, description) |
| `MultiStepForm` | Multi-step form with progress and htmx navigation |

## CRUD

| Export | Description |
|--------|-------------|
| `CRUDRouter` | Auto-register all CRUD routes for a model |
| `Storage` | Abstract storage interface (ABC) |
| `InMemoryStorage` | Dict-based in-memory storage |
| `Pagination` | Pagination button group component |
| `SQLModelStorage` | Async SQL storage via SQLModel (requires `kokage-ui[sql]`) |
| `create_tables` | Create all SQLModel tables |

## Admin Dashboard

| Export | Description |
|--------|-------------|
| `AdminSite` | Auto-generate admin panel from registered models |
| `ModelAdmin` | Model registration configuration (dataclass) |

## Authentication & Authorization

| Export | Description |
|--------|-------------|
| `LoginForm` | Pre-built login form card |
| `RegisterForm` | Pre-built registration form card |
| `UserMenu` | User dropdown menu for NavBar |
| `RoleGuard` | Server-side role-based content guard |
| `protected` | Route protection decorator (auth + role check) |

## Theme

| Export | Description |
|--------|-------------|
| `DarkModeToggle` | Light/dark theme toggle with sun/moon icons |
| `ThemeSwitcher` | Theme selector dropdown with color previews |

## Notifications

| Export | Description |
|--------|-------------|
| `Notifier` | Server-side SSE notification dispatcher |
| `NotificationStream` | Client-side SSE listener with toast display |

## Data Display

| Export | Description |
|--------|-------------|
| `Chart` | Chart.js chart (line, bar, pie, doughnut, radar, scatter) |
| `CodeBlock` | Syntax-highlighted code block (Highlight.js) |
| `Markdown` | Server-side Markdown rendering (requires `kokage-ui[markdown]`) |

## AI Chat

| Export | Description |
|--------|-------------|
| `ChatView` | Streaming chat UI with DaisyUI chat bubbles |
| `ChatMessage` | Chat message dataclass (role, content, name) |
| `chat_stream` | Convert async token generator to SSE StreamingResponse |
