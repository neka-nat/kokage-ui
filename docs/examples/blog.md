# Blog App

A blog application with Markdown rendering, Chart.js statistics, and tabbed content views.

## Run

```bash
uvicorn examples.blog:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

## Code

```python
--8<-- "examples/blog.py"
```

## Features Demonstrated

- **Markdown** — Server-side rendering with DaisyUI prose styling
- **CodeBlock** — Syntax-highlighted code blocks
- **Chart** — Bar, doughnut, and line charts via Chart.js
- **Tabs** — Content-mode tabs for article/source switching
- **Card / Badge / Breadcrumb** — DaisyUI components for layout
- **ThemeSwitcher** — Theme dropdown with custom theme subset

## Key Patterns

### Markdown Rendering

```python
Markdown(post["content"])  # Renders with fenced_code + tables extensions
```

Automatically applies `prose` classes for DaisyUI typography styling.

### Tabbed Content

```python
Tabs(
    tabs=[
        Tab(label="Article", content=Markdown(text), active=True),
        Tab(label="Source", content=CodeBlock(text, language="markdown")),
    ],
    variant="lifted",
)
```

Uses radio-based pure-CSS tabs (no JavaScript needed).

### Chart.js Integration

```python
Chart(
    type="bar",
    data={"labels": [...], "datasets": [{"label": "...", "data": [...]}]},
    height="300px",
)
```

Requires `Page(include_chartjs=True)` to load Chart.js from CDN.
