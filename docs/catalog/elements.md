# HTML Elements

Low-level HTML element wrappers. These map directly to standard HTML tags with Python-friendly attribute naming (`cls` → `class`, `hx_get` → `hx-get`).

## Button

Standard HTML `<button>` element.

### Preview

<iframe src="../previews/button.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Button("Click me", type="submit")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `*children` | `Any` | Button content |
| `type` | `str` | Button type (button/submit/reset) |

---

## Input

HTML `<input>` element. Void element (no children).

### Preview

<iframe src="../previews/input.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Input(type="text", name="username", placeholder="Enter name")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | `str` | Input type (text/email/password/number/...) |
| `name` | `str` | Field name |
| `placeholder` | `str` | Placeholder text |

---

## Select / Option

HTML `<select>` with `<option>` children.

### Preview

<iframe src="../previews/select-option.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Select(
    Option("Apple", value="apple"),
    Option("Banana", value="banana"),
    Option("Cherry", value="cherry"),
    name="fruit",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Field name |
| `*children` | `Option` | Option elements |

---

## Table

HTML `<table>` with thead/tbody structure.

### Preview

<iframe src="../previews/table.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Table(
    Thead(Tr(Th("Name"), Th("Age"))),
    Tbody(
        Tr(Td("Alice"), Td("30")),
        Tr(Td("Bob"), Td("25")),
    ),
)
```

---

## Form

HTML `<form>` container.

### Preview

<iframe src="../previews/form.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Form(
    Label("Name", Input(type="text", name="name")),
    Button("Submit", type="submit"),
    method="post",
)
```

---

## Ul / Ol

Unordered and ordered list elements.

### Preview

<iframe src="../previews/ul-ol.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Div(
    H3("Unordered"),
    Ul(Li("Item 1"), Li("Item 2"), Li("Item 3")),
    H3("Ordered"),
    Ol(Li("First"), Li("Second"), Li("Third")),
)
```

---

## Details / Summary

Disclosure widget with expandable content.

### Preview

<iframe src="../previews/details-summary.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Details(
    Summary("Click to expand"),
    P("Hidden content revealed on click."),
)
```

---

## Progress

HTML `<progress>` bar.

### Preview

<iframe src="../previews/progress.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Progress(value="70", max="100")
```

---

## Video

HTML `<video>` element.

### Preview

<iframe src="../previews/video.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Video(src="video.mp4", controls=True, width="320")
```

---

## Img

HTML `<img>` element.

### Preview

<iframe src="../previews/img.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Img(src="https://picsum.photos/300/200", alt="Sample")
```

---
