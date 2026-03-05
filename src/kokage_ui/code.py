"""Code block component with Highlight.js support.

Renders ``<pre><code>`` with optional syntax highlighting and copy button.
"""

from __future__ import annotations

import uuid
from typing import Any

from markupsafe import Markup, escape

from kokage_ui.elements import Component, _render_attrs


class CodeBlock(Component):
    """Syntax-highlighted code block using Highlight.js.

    Args:
        code: Source code string (will be HTML-escaped).
        language: Language for highlighting (None = auto-detect).
        copy_button: Show a copy-to-clipboard button.
    """

    tag = "div"

    def __init__(
        self,
        code: str,
        *,
        language: str | None = None,
        copy_button: bool = False,
        **attrs: Any,
    ) -> None:
        self._code = code
        self._language = language
        self._copy_button = copy_button
        self._attrs = attrs
        self._block_id = f"kokage-code-{uuid.uuid4().hex[:8]}"

    def render(self) -> str:
        escaped_code = escape(self._code)

        lang_cls = f"language-{self._language}" if self._language else ""
        code_tag = f'<code class="{lang_cls}">' if lang_cls else "<code>"

        parts: list[str] = [f"<pre>{code_tag}{escaped_code}</code></pre>"]

        if self._copy_button:
            # Encode the raw code for the clipboard using a data attribute
            parts.append(
                f'<button class="btn btn-ghost btn-xs absolute top-2 right-2" '
                f'data-code-target="{self._block_id}" '
                f'onclick="navigator.clipboard.writeText('
                f"document.getElementById('{self._block_id}').querySelector('code').textContent"
                f')">'
                f"Copy</button>"
            )

        # Inline script for hljs highlighting
        parts.append(
            f"<script>(function(){{"
            f"if(typeof hljs!=='undefined'){{"
            f"var el=document.getElementById('{self._block_id}').querySelector('code');"
            f"hljs.highlightElement(el);"
            f"}}"
            f"}})()</script>"
        )

        attrs = dict(self._attrs)
        base_cls = "relative"
        if "cls" in attrs:
            base_cls = f"{base_cls} {attrs.pop('cls')}"
        attrs["cls"] = base_cls
        attrs["id"] = self._block_id

        attr_str = _render_attrs(attrs)
        inner = "".join(parts)
        return Markup(f"<div{attr_str}>{inner}</div>")
