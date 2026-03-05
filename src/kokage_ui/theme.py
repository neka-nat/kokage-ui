"""Theme switching components for DaisyUI.

Provides DarkModeToggle (light/dark swap) and ThemeSwitcher (dropdown with
color previews). Both persist to localStorage and apply via data-theme.
"""

from __future__ import annotations

import uuid
from typing import Any

from kokage_ui.elements import (
    Component,
    Div,
    Input,
    Label,
    Raw,
    Script,
    Span,
)

_SUN_SVG = (
    '<svg class="swap-off fill-current {size}" xmlns="http://www.w3.org/2000/svg"'
    ' viewBox="0 0 24 24">'
    "<path"
    ' d="M5.64,17l-.71.71a1,1,0,0,0,0,1.41,1,1,0,0,0,1.41,0l.71-.71A1,1,0,0,0,5.64,17Z'
    "M5,12a1,1,0,0,0-1-1H3a1,1,0,0,0,0,2H4A1,1,0,0,0,5,12Zm7-7a1,1,0,0,0,1-1V3a1,1,0,0,0-2,0V4A1,1,0,0,0,12,5Z"
    "M5.64,7.05a1,1,0,0,0,.7.29,1,1,0,0,0,.71-.29,1,1,0,0,0,0-1.41l-.71-.71A1,1,0,0,0,4.93,6.34Z"
    "m12,.29a1,1,0,0,0,.7-.29l.71-.71a1,1,0,1,0-1.41-1.41L17,5.64a1,1,0,0,0,0,1.41,1,1,0,0,0,.71.29Z"
    "M21,11H20a1,1,0,0,0,0,2h1a1,1,0,0,0,0-2Zm-9,8a1,1,0,0,0-1,1v1a1,1,0,0,0,2,0V20A1,1,0,0,0,12,19Z"
    "M18.36,17A1,1,0,0,0,17,18.36l.71.71a1,1,0,0,0,1.41,0,1,1,0,0,0,0-1.41Z"
    'M12,6.5A5.5,5.5,0,1,0,17.5,12,5.51,5.51,0,0,0,12,6.5Zm0,9A3.5,3.5,0,1,1,15.5,12,3.5,3.5,0,0,1,12,15.5Z"/>'
    "</svg>"
)

_MOON_SVG = (
    '<svg class="swap-on fill-current {size}" xmlns="http://www.w3.org/2000/svg"'
    ' viewBox="0 0 24 24">'
    "<path"
    ' d="M21.64,13a1,1,0,0,0-1.05-.14,8.05,8.05,0,0,1-3.37.73A8.15,8.15,0,0,1,9.08,5.49a8.59,8.59,0,0,1,.25-2A1,1,0,0,0,8,2.36,10.14,10.14,0,1,0,22,14.05,1,1,0,0,0,21.64,13Z"/>'
    "</svg>"
)

_PALETTE_SVG = (
    '<svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none"'
    ' viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">'
    '<path stroke-linecap="round" stroke-linejoin="round"'
    ' d="M4.098 19.902a3.75 3.75 0 005.304 0l6.401-6.402M6.75 21A3.75 3.75 0 013 17.25V4.125C3'
    " 3.504 3.504 3 4.125 3h5.25c.621 0 1.125.504 1.125 1.125v4.072M6.75"
    " 21a3.75 3.75 0 003.75-3.75V8.197M6.75 21h13.125c.621 0"
    " 1.125-.504 1.125-1.125v-5.25c0-.621-.504-1.125-1.125-1.125h-4.072"
    'M10.5 8.197l2.88-2.88c.438-.439 1.15-.439 1.59 0l3.712 3.713c.44.44.44 1.152 0 1.59l-2.879 2.88M6.75 17.25h.008v.008H6.75v-.008z"/>'
    "</svg>"
)

ALL_THEMES = [
    "light", "dark", "cupcake", "bumblebee", "emerald",
    "corporate", "synthwave", "retro", "cyberpunk", "valentine",
    "halloween", "garden", "forest", "aqua", "lofi",
    "pastel", "fantasy", "wireframe", "black", "luxury",
    "dracula", "cmyk", "autumn", "business", "acid",
    "lemonade", "night", "coffee", "winter", "dim", "nord", "sunset",
]


def _merge_cls(base: str, extra: str | None) -> str:
    if extra:
        return f"{base} {extra}"
    return base


class DarkModeToggle(Component):
    """Light/dark theme toggle with sun/moon icons.

    Args:
        light_theme: Theme name for light mode (default: "light").
        dark_theme: Theme name for dark mode (default: "dark").
        key: localStorage key for persistence.
        size: Icon size class (e.g., "h-5 w-5", "h-6 w-6").
    """

    tag = "div"

    def __init__(
        self,
        *,
        light_theme: str = "light",
        dark_theme: str = "dark",
        key: str = "kokage-theme",
        size: str = "h-6 w-6",
        **attrs: Any,
    ) -> None:
        uid = uuid.uuid4().hex[:8]
        checkbox_id = f"kokage-dm-{uid}"

        sun = Raw(_SUN_SVG.replace("{size}", size))
        moon = Raw(_MOON_SVG.replace("{size}", size))

        checkbox = Input(type="checkbox", id=checkbox_id, cls="hidden")

        swap_label = Label(
            checkbox,
            sun,
            moon,
            cls="swap swap-rotate",
        )

        script_code = (
            "(function(){"
            f"var KEY='{key}',LIGHT='{light_theme}',DARK='{dark_theme}';"
            "var saved=localStorage.getItem(KEY);"
            "if(saved)document.documentElement.setAttribute('data-theme',saved);"
            f"var el=document.getElementById('{checkbox_id}');"
            "if(!el)return;"
            "el.checked=(saved||LIGHT)===DARK;"
            "el.addEventListener('change',function(){"
            "var t=this.checked?DARK:LIGHT;"
            "document.documentElement.setAttribute('data-theme',t);"
            "localStorage.setItem(KEY,t);"
            "});"
            "})();"
        )

        super().__init__(swap_label, Script(Raw(script_code)), **attrs)


class ThemeSwitcher(Component):
    """Theme selector dropdown with color previews.

    Args:
        themes: List of DaisyUI theme names. Default: all 32 built-in themes.
        current: Currently active theme name.
        label: Dropdown trigger text.
        size: Button size (xs, sm, md, lg).
        key: localStorage key for persistence.
    """

    tag = "div"

    def __init__(
        self,
        *,
        themes: list[str] | None = None,
        current: str = "light",
        label: str = "Theme",
        size: str = "sm",
        key: str = "kokage-theme",
        **attrs: Any,
    ) -> None:
        theme_list = themes if themes is not None else ALL_THEMES

        trigger = Div(
            Raw(_PALETTE_SVG),
            label,
            tabindex="0",
            role="button",
            cls=f"btn btn-ghost btn-{size} gap-1",
        )

        theme_buttons: list[Any] = []
        for theme_name in theme_list:
            preview = Span(
                Span(cls="bg-primary w-2 h-4 rounded-sm"),
                Span(cls="bg-secondary w-2 h-4 rounded-sm"),
                Span(cls="bg-accent w-2 h-4 rounded-sm"),
                Span(cls="bg-neutral w-2 h-4 rounded-sm"),
                cls="flex gap-0.5",
            )
            btn = Raw(
                f'<button data-theme="{theme_name}"'
                f" onclick=\"kokageSetTheme('{theme_name}')\""
                f' class="btn btn-ghost btn-sm justify-start gap-2 w-full">'
                f"{preview.render()}"
                f'<span class="flex-1 text-left text-base-content text-xs">'
                f"{theme_name}</span></button>"
            )
            theme_buttons.append(btn)

        dropdown_content = Div(
            Div(*theme_buttons, cls="grid grid-cols-1 gap-1"),
            tabindex="0",
            cls="dropdown-content bg-base-200 rounded-box z-10 w-56 p-2 shadow-lg max-h-80 overflow-y-auto",
        )

        script_code = (
            "(function(){"
            f"var KEY='{key}';"
            "var saved=localStorage.getItem(KEY);"
            "if(saved)document.documentElement.setAttribute('data-theme',saved);"
            "window.kokageSetTheme=function(t){"
            "document.documentElement.setAttribute('data-theme',t);"
            "localStorage.setItem(KEY,t);"
            "};"
            "})();"
        )

        attrs["cls"] = _merge_cls("dropdown dropdown-end", attrs.get("cls"))
        super().__init__(
            trigger, dropdown_content, Script(Raw(script_code)), **attrs
        )
