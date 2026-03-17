"""FilePreview component for rich rendering of tool results.

Detects content type (JSON, CSV, code, image, markdown, plain text) and
renders an appropriate rich preview. Used both as a standalone component
and integrated into AgentView's tool result panels.
"""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from markupsafe import Markup, escape

from kokage_ui.elements import Component, _render_attrs

# Image extensions for URL-based detection
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"}


def detect_content_type(
    content: str = "",
    *,
    hint: str = "",
    url: str = "",
) -> str:
    """Detect the content type for preview rendering.

    Args:
        content: The text content to analyze.
        hint: Explicit type hint (json, csv, python, javascript, etc.).
        url: URL for media detection by extension.

    Returns:
        One of: "json", "csv", "code", "image", "markdown", "text".
    """
    if hint:
        hint_lower = hint.lower()
        if hint_lower == "json":
            return "json"
        if hint_lower in ("csv", "tsv"):
            return "csv"
        if hint_lower in ("md", "markdown"):
            return "markdown"
        if hint_lower == "image":
            return "image"
        # Any other hint is treated as a code language
        return "code"

    if url:
        lower_url = url.lower().split("?")[0]
        for ext in _IMAGE_EXTS:
            if lower_url.endswith(ext):
                return "image"

    if not content:
        return "text"

    stripped = content.strip()

    # Try JSON
    if stripped and stripped[0] in ("{", "["):
        try:
            json.loads(stripped)
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass

    # Try CSV (heuristic: multiple lines with consistent comma/tab counts)
    lines = stripped.split("\n")
    if len(lines) >= 2:
        first_commas = lines[0].count(",")
        first_tabs = lines[0].count("\t")
        if first_commas >= 1 and all(
            line.count(",") == first_commas for line in lines[1:4] if line.strip()
        ):
            return "csv"
        if first_tabs >= 1 and all(
            line.count("\t") == first_tabs for line in lines[1:4] if line.strip()
        ):
            return "csv"

    return "text"


def render_json_tree(data: Any, max_depth: int = 5, _depth: int = 0) -> str:
    """Render a JSON value as a nested collapsible HTML tree.

    Args:
        data: Parsed JSON data.
        max_depth: Maximum nesting depth before truncation.
        _depth: Internal recursion depth tracker.

    Returns:
        HTML string.
    """
    if _depth >= max_depth:
        return f'<span class="text-base-content/50">...</span>'

    if isinstance(data, dict):
        if not data:
            return '<span class="text-base-content/60">{}</span>'
        items = []
        for key, val in data.items():
            key_escaped = escape(str(key))
            val_html = render_json_tree(val, max_depth, _depth + 1)
            items.append(
                f'<div class="ml-4">'
                f'<span class="text-info font-medium">"{key_escaped}"</span>: '
                f"{val_html}"
                f"</div>"
            )
        inner = "".join(items)
        if _depth == 0:
            return f'<div class="font-mono text-xs">{{{inner}}}</div>'
        return (
            f'<details class="inline"><summary class="cursor-pointer">'
            f"{{...}}</summary>{inner}</details>"
        )

    if isinstance(data, list):
        if not data:
            return '<span class="text-base-content/60">[]</span>'
        items = []
        for i, val in enumerate(data):
            val_html = render_json_tree(val, max_depth, _depth + 1)
            items.append(f'<div class="ml-4">{val_html},</div>')
        inner = "".join(items)
        if _depth == 0:
            return f'<div class="font-mono text-xs">[{inner}]</div>'
        return (
            f'<details class="inline"><summary class="cursor-pointer">'
            f"[{len(data)} items]</summary>{inner}</details>"
        )

    if isinstance(data, str):
        return f'<span class="text-success">"{escape(data)}"</span>'
    if isinstance(data, bool):
        return f'<span class="text-warning">{str(data).lower()}</span>'
    if data is None:
        return '<span class="text-base-content/50">null</span>'
    # numbers
    return f'<span class="text-secondary">{escape(str(data))}</span>'


def render_csv_table(content: str, max_rows: int = 100) -> str:
    """Render CSV content as a DaisyUI table.

    Args:
        content: CSV text content.
        max_rows: Maximum rows to display.

    Returns:
        HTML string.
    """
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        return f'<pre class="bg-base-300 p-2 rounded text-xs whitespace-pre-wrap">{escape(content)}</pre>'

    header = rows[0]
    body_rows = rows[1:]
    total_rows = len(body_rows)
    truncated = total_rows > max_rows
    if truncated:
        body_rows = body_rows[:max_rows]

    # Build table
    th_cells = "".join(f"<th>{escape(h)}</th>" for h in header)
    body_html = ""
    for row in body_rows:
        td_cells = "".join(f"<td>{escape(c)}</td>" for c in row)
        body_html += f"<tr>{td_cells}</tr>"

    html = (
        f'<div class="overflow-x-auto max-h-64">'
        f'<table class="table table-xs table-zebra">'
        f"<thead><tr>{th_cells}</tr></thead>"
        f"<tbody>{body_html}</tbody>"
        f"</table>"
    )
    if truncated:
        remaining = total_rows - max_rows
        html += f'<div class="text-xs text-base-content/50 mt-1">... and {remaining} more rows</div>'
    html += "</div>"
    return html


def render_preview(
    content: str = "",
    *,
    hint: str = "",
    url: str = "",
    language: str = "",
    max_depth: int = 5,
    max_rows: int = 100,
) -> str:
    """Render content with appropriate rich preview.

    Args:
        content: Text content to render.
        hint: Content type hint.
        url: URL for image/media preview.
        language: Code language (used when hint indicates code).
        max_depth: Max JSON tree depth.
        max_rows: Max CSV table rows.

    Returns:
        HTML string.
    """
    content_type = detect_content_type(content, hint=hint, url=url)

    if content_type == "json":
        try:
            data = json.loads(content.strip())
            return render_json_tree(data, max_depth=max_depth)
        except (json.JSONDecodeError, ValueError):
            pass

    if content_type == "csv":
        return render_csv_table(content, max_rows=max_rows)

    if content_type == "code":
        lang = language or hint
        lang_cls = f' class="language-{escape(lang)}"' if lang else ""
        return (
            f'<pre class="bg-base-300 p-2 rounded mt-1 text-xs">'
            f"<code{lang_cls}>{escape(content)}</code></pre>"
        )

    if content_type == "image":
        src = escape(url or content)
        return (
            f'<img src="{src}" class="max-w-full max-h-64 rounded mt-1" '
            f'loading="lazy" />'
        )

    if content_type == "markdown":
        # Server-side: just wrap in a div with prose class;
        # marked.js will render it client-side if available
        return (
            f'<div class="prose prose-sm max-w-none mt-1">{escape(content)}</div>'
        )

    # Plain text fallback
    return (
        f'<pre class="bg-base-300 p-2 rounded mt-1 text-xs'
        f' whitespace-pre-wrap">{escape(content)}</pre>'
    )


# JavaScript function for client-side preview rendering in AgentView.
# This is embedded in the AgentView inline script.
JS_PREVIEW_RENDERER = """\
function detectType(text, hint) {
  if (hint) {
    var h = hint.toLowerCase();
    if (h === 'json') return 'json';
    if (h === 'csv' || h === 'tsv') return 'csv';
    if (h === 'image') return 'image';
    if (h === 'md' || h === 'markdown') return 'markdown';
    return 'code';
  }
  if (!text) return 'text';
  var s = text.trim();
  if (s[0] === '{' || s[0] === '[') {
    try { JSON.parse(s); return 'json'; } catch(e) {}
  }
  var lines = s.split('\\n');
  if (lines.length >= 2) {
    var c = (lines[0].match(/,/g) || []).length;
    var t = (lines[0].match(/\\t/g) || []).length;
    if (c >= 1) {
      var ok = true;
      for (var i = 1; i < Math.min(lines.length, 4); i++) {
        if (lines[i].trim() && (lines[i].match(/,/g) || []).length !== c) { ok = false; break; }
      }
      if (ok) return 'csv';
    }
    if (t >= 1) {
      var ok2 = true;
      for (var j = 1; j < Math.min(lines.length, 4); j++) {
        if (lines[j].trim() && (lines[j].match(/\\t/g) || []).length !== t) { ok2 = false; break; }
      }
      if (ok2) return 'csv';
    }
  }
  return 'text';
}

function renderJsonTree(data, depth, maxDepth) {
  if (depth >= maxDepth) return '<span class="text-base-content/50">...</span>';
  if (data === null) return '<span class="text-base-content/50">null</span>';
  if (typeof data === 'boolean') return '<span class="text-warning">' + data + '</span>';
  if (typeof data === 'number') return '<span class="text-secondary">' + data + '</span>';
  if (typeof data === 'string') return '<span class="text-success">"' + escapeHtml(data) + '"</span>';
  if (Array.isArray(data)) {
    if (!data.length) return '<span class="text-base-content/60">[]</span>';
    var items = '';
    for (var i = 0; i < data.length; i++) {
      items += '<div class="ml-4">' + renderJsonTree(data[i], depth + 1, maxDepth) + ',</div>';
    }
    if (depth === 0) return '<div class="font-mono text-xs">[' + items + ']</div>';
    return '<details class="inline"><summary class="cursor-pointer">[' + data.length + ' items]</summary>' + items + '</details>';
  }
  if (typeof data === 'object') {
    var keys = Object.keys(data);
    if (!keys.length) return '<span class="text-base-content/60">{}</span>';
    var items2 = '';
    for (var k = 0; k < keys.length; k++) {
      items2 += '<div class="ml-4"><span class="text-info font-medium">"' + escapeHtml(keys[k]) + '"</span>: ' + renderJsonTree(data[keys[k]], depth + 1, maxDepth) + '</div>';
    }
    if (depth === 0) return '<div class="font-mono text-xs">{' + items2 + '}</div>';
    return '<details class="inline"><summary class="cursor-pointer">{...}</summary>' + items2 + '</details>';
  }
  return escapeHtml(String(data));
}

function renderCsvTable(text, maxRows) {
  var lines = text.trim().split('\\n');
  if (lines.length < 2) return '<pre class="bg-base-300 p-2 rounded text-xs whitespace-pre-wrap">' + escapeHtml(text) + '</pre>';
  var header = lines[0].split(',');
  var th = '';
  for (var i = 0; i < header.length; i++) th += '<th>' + escapeHtml(header[i].trim()) + '</th>';
  var body = '';
  var shown = Math.min(lines.length - 1, maxRows);
  for (var j = 1; j <= shown; j++) {
    var cols = lines[j].split(',');
    var tds = '';
    for (var k = 0; k < cols.length; k++) tds += '<td>' + escapeHtml(cols[k].trim()) + '</td>';
    body += '<tr>' + tds + '</tr>';
  }
  var html = '<div class="overflow-x-auto max-h-64"><table class="table table-xs table-zebra"><thead><tr>' + th + '</tr></thead><tbody>' + body + '</tbody></table>';
  if (lines.length - 1 > maxRows) html += '<div class="text-xs text-base-content/50 mt-1">... and ' + (lines.length - 1 - maxRows) + ' more rows</div>';
  html += '</div>';
  return html;
}

function renderPreview(text, hint) {
  var type = detectType(text, hint);
  if (type === 'json') {
    try {
      var data = JSON.parse(text.trim());
      return renderJsonTree(data, 0, 5);
    } catch(e) {}
  }
  if (type === 'csv') return renderCsvTable(text, 100);
  if (type === 'code') {
    var lang = hint || '';
    var cls = lang ? ' class="language-' + escapeHtml(lang) + '"' : '';
    return '<pre class="bg-base-300 p-2 rounded mt-1 text-xs"><code' + cls + '>' + escapeHtml(text) + '</code></pre>';
  }
  if (type === 'image') {
    return '<img src="' + escapeHtml(text) + '" class="max-w-full max-h-64 rounded mt-1" loading="lazy" />';
  }
  return '<pre class="bg-base-300 p-2 rounded mt-1 text-xs whitespace-pre-wrap">' + escapeHtml(text) + '</pre>';
}
"""


class FilePreview(Component):
    """Rich preview component for structured content.

    Auto-detects content type and renders appropriate preview:
    JSON tree, CSV table, syntax-highlighted code, image, or plain text.

    Args:
        content: Text content to preview.
        hint: Content type hint (json, csv, python, etc.).
        url: URL for image/media preview.
        language: Code language for syntax highlighting.
        max_depth: Max JSON tree nesting depth.
        max_rows: Max CSV table rows.
    """

    tag = "div"

    def __init__(
        self,
        content: str = "",
        *,
        hint: str = "",
        url: str = "",
        language: str = "",
        max_depth: int = 5,
        max_rows: int = 100,
        **attrs: Any,
    ) -> None:
        self._content = content
        self._hint = hint
        self._url = url
        self._language = language
        self._max_depth = max_depth
        self._max_rows = max_rows
        super().__init__(**attrs)

    def render(self) -> str:
        inner = render_preview(
            self._content,
            hint=self._hint,
            url=self._url,
            language=self._language,
            max_depth=self._max_depth,
            max_rows=self._max_rows,
        )
        attr_str = _render_attrs(self.attrs)
        return f"<div{attr_str}>{inner}</div>"
