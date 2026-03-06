# htmx Patterns

Ready-made htmx interaction patterns. These generate the correct `hx-*` attributes for common dynamic UI patterns. Note: previews show the static HTML output only.

## SearchFilter

Live search input with debounced htmx requests.

### Preview

<iframe src="../previews/searchfilter.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
SearchFilter(
    url="/api/search",
    target="#results",
    placeholder="Search users...",
    delay=300,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Search endpoint |
| `target` | `str` | Result target selector |
| `placeholder` | `str` | Input placeholder |
| `delay` | `int` | Debounce in ms (default: 300) |

---

## AutoRefresh

Periodically polls an endpoint to update content.

### Preview

<iframe src="../previews/autorefresh.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
AutoRefresh(
    P("Live data will appear here."),
    url="/api/status",
    interval=10,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Poll endpoint |
| `interval` | `int` | Seconds between polls (default: 5) |
| `target` | `str | None` | Target selector |
| `swap` | `str` | Swap method (default: "innerHTML") |

---

## ConfirmDelete

Delete button with browser confirmation dialog.

### Preview

<iframe src="../previews/confirmdelete.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
ConfirmDelete(
    "Delete Item",
    url="/api/items/1",
    confirm_message="Are you sure you want to delete this?",
    target="#item-1",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | DELETE endpoint |
| `confirm_message` | `str` | Confirmation dialog text |
| `target` | `str | None` | Target selector |
| `swap` | `str` | Swap method (default: "outerHTML") |

---

## InfiniteScroll

Load more content when scrolling to the bottom.

### Preview

<iframe src="../previews/infinitescroll.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
InfiniteScroll(
    url="/api/items?page=2",
    target="#item-list",
    swap="beforeend",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Next page endpoint |
| `target` | `str | None` | Insert target |
| `swap` | `str` | Swap method (default: "beforeend") |
| `indicator` | `Any` | Loading indicator |

---
