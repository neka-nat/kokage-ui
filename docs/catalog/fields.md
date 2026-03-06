# Field Components

Specialized form field components for rich input experiences. Some require external JS libraries (Quill, flatpickr, SortableJS).

## RichTextEditor

Quill-based rich text editor (requires Quill JS).

### Preview

<iframe src="../previews/richtexteditor.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
RichTextEditor(
    name="content",
    value="<p>Hello <strong>world</strong></p>",
    height="200px",
    placeholder="Write something...",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Form field name |
| `value` | `str` | Initial HTML content |
| `height` | `str` | Editor height (default: "300px") |
| `toolbar` | `str` | "standard" | "minimal" | "full" |

---

## DateTimePicker

Flatpickr-based date/time picker.

### Preview

<iframe src="../previews/datetimepicker.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
DateTimePicker(
    name="event_date",
    value="2025-01-01",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Form field name |
| `value` | `str` | Initial value |
| `field_config` | `DateField | TimeField | DateTimeField | None` | Field configuration |

---

## RepeaterInput

Dynamic list of input fields with add/remove.

### Preview

<iframe src="../previews/repeaterinput.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
RepeaterInput(
    name="tags",
    values=["Python", "FastAPI"],
    placeholder="Add tag...",
    add_label="+ Add Tag",
    max_items=5,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Form field name |
| `values` | `list[str] | None` | Initial values |
| `min_items` | `int` | Minimum rows |
| `max_items` | `int | None` | Maximum rows |
| `placeholder` | `str` | Input placeholder |
| `add_label` | `str` | Add button text (default: "Add") |

---

## TagInput

Tag/chip input with keyboard support.

### Preview

<iframe src="../previews/taginput.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
TagInput(
    name="skills",
    values=["Python", "JavaScript", "Go"],
    placeholder="Add skill...",
    color="primary",
    max_tags=10,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Form field name |
| `values` | `list[str] | None` | Initial tags |
| `placeholder` | `str` | Input placeholder |
| `max_tags` | `int | None` | Maximum number of tags |
| `color` | `str` | DaisyUI badge color (default: primary) |
| `separator` | `str` | Trigger character (default: ",") |

---

## SortableList

Drag-and-drop sortable list (requires SortableJS).

### Preview

<iframe src="../previews/sortablelist.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
SortableList(
    items=[
        {"id": "1", "label": "First item"},
        {"id": "2", "label": "Second item"},
        {"id": "3", "label": "Third item", "badge": "New"},
    ],
    url="/api/reorder",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `items` | `list[dict]` | Items with "id", "label", optional "badge" |
| `url` | `str` | POST endpoint for reorder |
| `handle` | `bool` | Show drag handle (default: True) |

---
