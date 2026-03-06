# Features

Higher-level feature components for authentication, theming, charting, and code display.

## LoginForm

Pre-built login form with username/password fields.

### Preview

<iframe src="../previews/loginform.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
LoginForm(
    action="/login",
    title="Sign In",
    register_url="/register",
    forgot_url="/forgot",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | `str` | Form action (default: "/login") |
| `title` | `str` | Form title (default: "Login") |
| `use_email` | `bool` | Use email field instead of username |
| `register_url` | `str | None` | Link to register page |
| `forgot_url` | `str | None` | Link to forgot password page |

---

## RegisterForm

Pre-built registration form.

### Preview

<iframe src="../previews/registerform.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
RegisterForm(
    action="/register",
    title="Create Account",
    login_url="/login",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | `str` | Form action (default: "/register") |
| `title` | `str` | Form title (default: "Register") |
| `login_url` | `str | None` | Link to login page |

---

## DarkModeToggle

Toggle button for light/dark theme switching.

### Preview

<iframe src="../previews/darkmodetoggle.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
DarkModeToggle(
    light_theme="light",
    dark_theme="dark",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `light_theme` | `str` | Light theme name (default: "light") |
| `dark_theme` | `str` | Dark theme name (default: "dark") |
| `key` | `str` | localStorage key |

---

## ThemeSwitcher

Dropdown for switching between multiple DaisyUI themes.

### Preview

<iframe src="../previews/themeswitcher.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
ThemeSwitcher(
    themes=["light", "dark", "cupcake", "bumblebee", "emerald"],
    default="light",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `themes` | `list[str]` | Available theme names |
| `default` | `str` | Default theme (default: "light") |

---

## Chart

Chart.js wrapper for line, bar, pie, and other charts.

### Preview

<iframe src="../previews/chart.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
Chart(
    type="bar",
    data={
        "labels": ["Jan", "Feb", "Mar", "Apr"],
        "datasets": [{
            "label": "Sales",
            "data": [12, 19, 3, 5],
        }],
    },
    height="300px",
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | `str` | "line" | "bar" | "pie" | "doughnut" | "radar" | "scatter" |
| `data` | `dict` | Chart.js data object |
| `options` | `dict | None` | Chart.js options |
| `width` | `str` | CSS width (default: "100%") |
| `height` | `str` | CSS height (default: "400px") |

---

## CodeBlock

Syntax-highlighted code display (requires Highlight.js).

### Preview

<iframe src="../previews/codeblock.html" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;" loading="lazy"></iframe>

### Code

```python
    CodeBlock(
        """def hello():
print("Hello, world!")""",
        language="python",
        copy_button=True,
    )
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | `str` | Source code to display |
| `language` | `str | None` | Language for syntax highlighting |
| `copy_button` | `bool` | Show copy button |

---
