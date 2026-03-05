# HTML Elements

kokage-ui provides a class-based HTML generation system. Every HTML element is a Python class. Children are positional arguments, attributes are keyword arguments.

## Component Base Class

All elements inherit from `Component`:

```python
from kokage_ui import Component

class Component:
    tag: str = "div"

    def __init__(self, *children, **attrs):
        ...

    def render(self) -> str:
        ...
```

Usage:

```python
from kokage_ui import Div, P, H1

# Children are positional args
Div(H1("Title"), P("Paragraph"))
# → <div><h1>Title</h1><p>Paragraph</p></div>

# Attributes are keyword args
Div("Hello", id="main", cls="container")
# → <div id="main" class="container">Hello</div>
```

## Attribute Conversion Rules

Python keyword arguments are automatically converted to HTML attributes:

| Python | HTML | Rule |
|--------|------|------|
| `cls="container"` | `class="container"` | Reserved word mapping |
| `html_for="name"` | `for="name"` | Reserved word mapping |
| `http_equiv="X-UA"` | `http-equiv="X-UA"` | Reserved word mapping |
| `hx_get="/api"` | `hx-get="/api"` | Underscore → hyphen |
| `data_value="1"` | `data-value="1"` | Underscore → hyphen |

### Boolean Attributes

```python
Input(type="checkbox", checked=True, disabled=True)
# → <input type="checkbox" checked disabled />

Input(type="text", disabled=False)
# → <input type="text" />  (False values are omitted)
```

### Dict Values (JSON)

```python
Div(hx_vals={"key": "value"})
# → <div hx-vals='{"key": "value"}'></div>
```

## Void Elements

Elements like `<br>`, `<hr>`, `<img>`, `<input>` are self-closing and cannot have children:

```python
from kokage_ui import Br, Hr, Img, Input

Img(src="/photo.jpg", alt="Photo")
# → <img src="/photo.jpg" alt="Photo" />

Input(type="text", name="q", placeholder="Search")
# → <input type="text" name="q" placeholder="Search" />
```

## Raw HTML

Use `Raw` to insert trusted HTML without escaping:

```python
from kokage_ui import Raw, Div

Div(Raw("<b>Bold</b>"))
# → <div><b>Bold</b></div>
```

!!! warning
    Only use `Raw` with trusted content. All other children are escaped via `markupsafe` to prevent XSS.

## Element Reference

### Sections / Containers

| Class | Tag |
|-------|-----|
| `Div` | `<div>` |
| `Span` | `<span>` |
| `Section` | `<section>` |
| `Article` | `<article>` |
| `Aside` | `<aside>` |
| `Header` | `<header>` |
| `Footer` | `<footer>` |
| `Main` | `<main>` |
| `Nav` | `<nav>` |

### Text

| Class | Tag |
|-------|-----|
| `P` | `<p>` |
| `H1` – `H6` | `<h1>` – `<h6>` |
| `Strong` | `<strong>` |
| `Em` | `<em>` |
| `Small` | `<small>` |
| `Pre` | `<pre>` |
| `Code` | `<code>` |
| `Blockquote` | `<blockquote>` |

### Links / Media

| Class | Tag |
|-------|-----|
| `A` | `<a>` |
| `Img` | `<img>` (void) |
| `Br` | `<br>` (void) |
| `Hr` | `<hr>` (void) |

### Lists

| Class | Tag |
|-------|-----|
| `Ul` | `<ul>` |
| `Ol` | `<ol>` |
| `Li` | `<li>` |

### Tables

| Class | Tag |
|-------|-----|
| `Table` | `<table>` |
| `Thead` | `<thead>` |
| `Tbody` | `<tbody>` |
| `Tfoot` | `<tfoot>` |
| `Tr` | `<tr>` |
| `Th` | `<th>` |
| `Td` | `<td>` |

### Forms

| Class | Tag |
|-------|-----|
| `Form` | `<form>` |
| `Button` | `<button>` |
| `Input` | `<input>` (void) |
| `Textarea` | `<textarea>` |
| `Select` | `<select>` |
| `Option` | `<option>` |
| `Label` | `<label>` |
| `Fieldset` | `<fieldset>` |
| `Legend` | `<legend>` |

### Document / Meta

| Class | Tag |
|-------|-----|
| `Script` | `<script>` |
| `Style` | `<style>` |
| `Link` | `<link>` (void) |
| `Meta` | `<meta>` (void) |
| `Title` | `<title>` |
| `Head` | `<head>` |
| `Body` | `<body>` |
| `Html` | `<html>` |

### Other

| Class | Tag |
|-------|-----|
| `Figure` | `<figure>` |
| `Figcaption` | `<figcaption>` |
| `Details` | `<details>` |
| `Summary` | `<summary>` |
| `Dialog` | `<dialog>` |
| `Progress` | `<progress>` |

## Nesting and Composition

Components can be freely nested:

```python
from kokage_ui import Div, Ul, Li, A, Strong

nav = Div(
    Ul(
        Li(A("Home", href="/")),
        Li(A("About", href="/about")),
        Li(A(Strong("Contact"), href="/contact")),
    ),
    cls="navbar",
)
```

Lists and tuples are flattened:

```python
items = ["Apple", "Banana", "Cherry"]
Ul(*[Li(item) for item in items])
```
