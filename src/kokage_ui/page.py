"""Full-page HTML document generation.

Generates complete HTML documents with htmx + DaisyUI CDN links.
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup, escape

from kokage_ui.elements import Component, _render_child

# CDN / static paths
HTMX_JS_PATH = "/_kokage/static/htmx.min.js"
HTMX_SSE_CDN = "https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4/sse.js"
DAISYUI_CSS_CDN = "https://cdn.jsdelivr.net/npm/daisyui@5"
TAILWIND_CDN = "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"


class Page:
    """Full HTML document.

    Generates a complete <!DOCTYPE html> document with htmx (local bundle)
    and DaisyUI (CDN) automatically loaded.

    Args:
        *children: Components to place in the body.
        title: Page title (<title> tag).
        theme: DaisyUI theme name (data-theme attribute).
        head_extra: Additional elements for <head>.
        lang: lang attribute for <html> (default: "ja").
        include_sse: Whether to load htmx SSE extension.
    """

    def __init__(
        self,
        *children: Any,
        title: str = "",
        theme: str = "light",
        head_extra: list[Any] | None = None,
        lang: str = "ja",
        include_sse: bool = False,
    ) -> None:
        self.children = children
        self.title = title
        self.theme = theme
        self.head_extra = head_extra or []
        self.lang = lang
        self.include_sse = include_sse

    def render(self) -> str:
        """Generate full HTML document string."""
        head_parts = [
            '<meta charset="UTF-8" />',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0" />',
            f"<title>{escape(self.title)}</title>",
            f'<link href="{DAISYUI_CSS_CDN}" rel="stylesheet" type="text/css" />',
            f'<script src="{TAILWIND_CDN}"></script>',
            f'<script src="{HTMX_JS_PATH}"></script>',
        ]

        if self.include_sse:
            head_parts.append(f'<script src="{HTMX_SSE_CDN}"></script>')

        for extra in self.head_extra:
            head_parts.append(_render_child(extra))

        head_html = "\n    ".join(head_parts)
        body_html = "\n".join(_render_child(c) for c in self.children if c is not None)

        return Markup(
            f"<!DOCTYPE html>\n"
            f'<html lang="{escape(self.lang)}" data-theme="{escape(self.theme)}">\n'
            f"<head>\n    {head_html}\n</head>\n"
            f"<body>\n{body_html}\n</body>\n"
            f"</html>"
        )

    def __str__(self) -> str:
        return self.render()

    def __html__(self) -> str:
        return self.render()
