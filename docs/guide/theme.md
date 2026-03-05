# Theme System

kokage-ui supports DaisyUI's theme system with two components for runtime theme switching: `DarkModeToggle` for light/dark toggle and `ThemeSwitcher` for selecting from all 32 DaisyUI themes. Both persist the user's choice via localStorage.

## DarkModeToggle

A sun/moon toggle switch for light and dark themes:

```python
from kokage_ui import DarkModeToggle, NavBar, A

NavBar(
    start=A("My App", href="/"),
    end=DarkModeToggle(),
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `light_theme` | str | Light theme name (default: `"light"`) |
| `dark_theme` | str | Dark theme name (default: `"dark"`) |
| `key` | str | localStorage key (default: `"kokage-theme"`) |
| `size` | str | Icon size classes (default: `"h-6 w-6"`) |

### Custom Theme Pair

```python
DarkModeToggle(light_theme="corporate", dark_theme="business")
```

## ThemeSwitcher

A dropdown with all available themes, each showing a color preview:

```python
from kokage_ui import ThemeSwitcher

ThemeSwitcher(size="sm")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `themes` | list[str] \| None | Theme list (default: all 32 DaisyUI themes) |
| `current` | str | Currently active theme (default: `"light"`) |
| `label` | str | Dropdown trigger text (default: `"Theme"`) |
| `size` | str | Button size — xs, sm, md, lg (default: `"sm"`) |
| `key` | str | localStorage key (default: `"kokage-theme"`) |

### Custom Theme Set

```python
ThemeSwitcher(themes=["corporate", "business", "nord", "dracula"])
```

## NavBar Integration

Both components work well in the NavBar:

```python
NavBar(
    start=A("My App", href="/", cls="text-xl font-bold"),
    end=Div(
        DarkModeToggle(),
        ThemeSwitcher(size="sm"),
        cls="flex items-center gap-2",
    ),
)
```

## How It Works

1. Both components use `document.documentElement.setAttribute('data-theme', name)` to switch themes
2. Theme choice is saved to `localStorage` with the configured key
3. On page load, an inline script restores the saved theme before rendering
4. Both components use the same localStorage key by default, so they stay in sync
5. No server-side changes needed — everything is client-side

## Available Themes

DaisyUI provides 32 built-in themes:

`light`, `dark`, `cupcake`, `bumblebee`, `emerald`, `corporate`, `synthwave`, `retro`, `cyberpunk`, `valentine`, `halloween`, `garden`, `forest`, `aqua`, `lofi`, `pastel`, `fantasy`, `wireframe`, `black`, `luxury`, `dracula`, `cmyk`, `autumn`, `business`, `acid`, `lemonade`, `night`, `coffee`, `winter`, `dim`, `nord`, `sunset`
