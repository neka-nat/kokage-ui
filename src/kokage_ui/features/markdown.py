"""Markdown rendering component.

Server-side Markdown to HTML using the ``markdown`` library,
styled with DaisyUI/Tailwind ``prose`` classes.
"""

from __future__ import annotations

import re
from typing import Any

from markupsafe import Markup

from kokage_ui.elements import Component, _render_attrs

# Tags and attributes stripped when trusted=False
_UNSAFE_TAG_RE = re.compile(r"<(script|style|iframe)\b[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_ON_ATTR_RE = re.compile(r'\s+on\w+\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', re.IGNORECASE)


def _sanitize_html(html: str) -> str:
    """Strip dangerous tags and on* attributes from rendered HTML."""
    html = _UNSAFE_TAG_RE.sub("", html)
    html = _ON_ATTR_RE.sub("", html)
    return html


class Markdown(Component):
    """Render Markdown text as styled HTML.

    Requires the ``markdown`` package (``pip install markdown``).

    Args:
        text: Markdown source text.
        extensions: Markdown extensions (default: fenced_code + tables).
        trusted: If False (default), strip <script>/<style>/<iframe> and on* attrs.
        prose_size: Tailwind prose size class (default "prose-base").
    """

    tag = "div"

    def __init__(
        self,
        text: str,
        *,
        extensions: list[str] | None = None,
        trusted: bool = False,
        prose_size: str = "prose-base",
        **attrs: Any,
    ) -> None:
        self._text = text
        self._extensions = extensions if extensions is not None else ["fenced_code", "tables"]
        self._trusted = trusted
        self._prose_size = prose_size
        self._attrs = attrs

    def render(self) -> str:
        try:
            import markdown as md_lib
        except ImportError:
            raise ImportError(
                "The 'markdown' package is required for the Markdown component. "
                "Install it with: pip install markdown"
            ) from None

        rendered = md_lib.markdown(self._text, extensions=self._extensions)

        if not self._trusted:
            rendered = _sanitize_html(rendered)

        attrs = dict(self._attrs)
        base_cls = f"prose {self._prose_size} max-w-none"
        if "cls" in attrs:
            base_cls = f"{base_cls} {attrs.pop('cls')}"
        attrs["cls"] = base_cls

        attr_str = _render_attrs(attrs)
        return Markup(f"<div{attr_str}>{rendered}</div>")
