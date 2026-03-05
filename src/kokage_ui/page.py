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
CHARTJS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4"
HIGHLIGHTJS_CDN = "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build"
HIGHLIGHTJS_CSS = f"{HIGHLIGHTJS_CDN}/styles/github-dark.min.css"
HIGHLIGHTJS_JS = f"{HIGHLIGHTJS_CDN}/highlight.min.js"
SORTABLEJS_CDN = "https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js"


_TOAST_SCRIPT = """\
<script>
(function(){
  var p = new URLSearchParams(window.location.search);
  var msg = p.get('_toast');
  if (!msg) return;
  var t = p.get('_toast_type') || 'success';
  var cls = {'success':'alert-success','error':'alert-error','warning':'alert-warning','info':'alert-info'}[t] || 'alert-info';
  var safe = msg.replace(/</g, '&lt;');
  var c = document.getElementById('kokage-toast');
  if (!c) return;
  c.innerHTML = '<div class="alert ' + cls + '" role="alert"><span>' + safe + '</span></div>';
  c.style.display = '';
  setTimeout(function(){ c.style.display = 'none'; }, 3000);
  p.delete('_toast'); p.delete('_toast_type');
  var u = window.location.pathname;
  var s = p.toString();
  if (s) u += '?' + s;
  window.history.replaceState({}, '', u);
})();
</script>"""

_TOAST_CONTAINER = '<div id="kokage-toast" class="toast toast-end toast-top z-50" style="display:none"></div>'


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
        include_toast: Whether to include toast notification support.
        include_chartjs: Whether to load Chart.js from CDN.
        include_highlightjs: Whether to load Highlight.js from CDN.
        include_sortablejs: Whether to load SortableJS from CDN.
    """

    def __init__(
        self,
        *children: Any,
        title: str = "",
        theme: str = "light",
        head_extra: list[Any] | None = None,
        lang: str = "ja",
        include_sse: bool = False,
        include_toast: bool = False,
        include_chartjs: bool = False,
        include_highlightjs: bool = False,
        include_sortablejs: bool = False,
    ) -> None:
        self.children = children
        self.title = title
        self.theme = theme
        self.head_extra = head_extra or []
        self.lang = lang
        self.include_sse = include_sse
        self.include_toast = include_toast
        self.include_chartjs = include_chartjs
        self.include_highlightjs = include_highlightjs
        self.include_sortablejs = include_sortablejs

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

        if self.include_chartjs:
            head_parts.append(f'<script src="{CHARTJS_CDN}"></script>')

        if self.include_highlightjs:
            head_parts.append(f'<link rel="stylesheet" href="{HIGHLIGHTJS_CSS}" />')
            head_parts.append(f'<script src="{HIGHLIGHTJS_JS}"></script>')
            head_parts.append(
                '<script>document.addEventListener("htmx:afterSwap",function(e){'
                'e.detail.elt.querySelectorAll("pre code").forEach(function(el){hljs.highlightElement(el);});'
                '});</script>'
            )

        if self.include_sortablejs:
            head_parts.append(f'<script src="{SORTABLEJS_CDN}"></script>')

        for extra in self.head_extra:
            head_parts.append(_render_child(extra))

        head_html = "\n    ".join(head_parts)
        body_html = "\n".join(_render_child(c) for c in self.children if c is not None)

        if self.include_toast:
            body_html += f"\n{_TOAST_CONTAINER}\n{_TOAST_SCRIPT}"

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
