# API Reference

Quick reference of all exports from `kokage_ui`.

## Core

| Export | Module | Description |
|--------|--------|-------------|
| `KokageUI` | `core` | FastAPI integration — `page()`, `fragment()`, `crud()` decorators |
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

## Pydantic Model → UI

| Export | Description |
|--------|-------------|
| `ModelForm` | Auto-generate form from BaseModel |
| `ModelTable` | Auto-generate table from BaseModel + rows |
| `ModelDetail` | Auto-generate detail card from model instance |

## htmx Helpers

| Export | Description |
|--------|-------------|
| `AutoRefresh` | Poll URL at interval (`hx-trigger="every Ns"`) |
| `SearchFilter` | Debounced search input (`hx-trigger="keyup changed delay:Nms"`) |
| `InfiniteScroll` | Load on scroll (`hx-trigger="revealed"`) |
| `SSEStream` | Server-Sent Events receiver (htmx SSE extension) |
| `ConfirmDelete` | Delete button with confirmation (`hx-confirm` + `hx-delete`) |
| `HxSwapOOB` | Out-of-Band swap (`hx-swap-oob`) |

## CRUD

| Export | Description |
|--------|-------------|
| `CRUDRouter` | Auto-register all CRUD routes for a model |
| `Storage` | Abstract storage interface (ABC) |
| `InMemoryStorage` | Dict-based in-memory storage |
| `Pagination` | Pagination button group component |
