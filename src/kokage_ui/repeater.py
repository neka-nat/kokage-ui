"""Repeater field for dynamic add/remove form rows.

Provides RepeaterField annotation for Pydantic models and
RepeaterInput component that renders multiple input elements
with the same name attribute for list field handling.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from markupsafe import Markup, escape

from kokage_ui.elements import Component


@dataclass(frozen=True)
class RepeaterField:
    """Annotated marker for repeater (dynamic list) fields.

    Usage:
        class Recipe(BaseModel):
            tags: Annotated[list[str], RepeaterField()] = []
            steps: Annotated[list[str], RepeaterField(
                add_label="Add step", placeholder="Step description...",
            )] = []
    """

    min_items: int = 0
    max_items: int | None = None
    placeholder: str = ""
    add_label: str = "Add"


class RepeaterInput(Component):
    """Dynamic add/remove input rows for list fields.

    Renders multiple <input> elements with the same name attribute.
    Inline JS handles add/remove without server round-trips.

    Args:
        name: Form field name (shared across all rows).
        values: Initial list of values.
        input_type: HTML input type (default "text").
        min_items: Minimum number of rows.
        max_items: Maximum number of rows (None = unlimited).
        placeholder: Input placeholder text.
        add_label: Label for the add button.
        repeater_id: HTML id prefix (auto-generated if None).
    """

    tag = "div"

    def __init__(
        self,
        *,
        name: str = "",
        values: list[str] | None = None,
        input_type: str = "text",
        min_items: int = 0,
        max_items: int | None = None,
        placeholder: str = "",
        add_label: str = "Add",
        repeater_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self._name = name
        self._values = values or []
        self._input_type = input_type
        self._min_items = min_items
        self._max_items = max_items
        self._placeholder = placeholder
        self._add_label = add_label
        self._repeater_id = repeater_id or f"kokage-repeater-{uuid.uuid4().hex[:8]}"
        self._attrs = attrs

    def render(self) -> str:
        from kokage_ui.elements import _render_attrs

        rid = self._repeater_id
        uid = rid.replace("-", "_")
        name_esc = escape(self._name)
        placeholder_esc = escape(self._placeholder)
        input_type_esc = escape(self._input_type)
        max_items_js = "null" if self._max_items is None else str(self._max_items)

        # Build existing rows from values
        rows_html_parts: list[str] = []

        # Ensure at least min_items rows
        values = list(self._values)
        while len(values) < self._min_items:
            values.append("")

        for val in values:
            val_esc = escape(str(val))
            rows_html_parts.append(
                f'<div class="flex items-center gap-2 mb-2" data-repeater-row>'
                f'<input type="{input_type_esc}" name="{name_esc}" value="{val_esc}" '
                f'placeholder="{placeholder_esc}" class="input input-bordered w-full" />'
                f'<button type="button" class="btn btn-ghost btn-sm" '
                f'data-repeater-remove onclick="{uid}_remove(this)">'
                f"\u2715</button>"
                f"</div>"
            )

        rows_html = "".join(rows_html_parts)

        # Template for new rows
        tmpl_html = (
            f'<div class="flex items-center gap-2 mb-2" data-repeater-row>'
            f'<input type="{input_type_esc}" name="{name_esc}" value="" '
            f'placeholder="{placeholder_esc}" class="input input-bordered w-full" />'
            f'<button type="button" class="btn btn-ghost btn-sm" '
            f'data-repeater-remove onclick="{uid}_remove(this)">'
            f"\u2715</button>"
            f"</div>"
        )

        add_label_esc = escape(self._add_label)

        script = (
            f"<script>(function(){{"
            f"var container=document.getElementById('{rid}-rows');"
            f"var tmpl=document.getElementById('{rid}-tmpl');"
            f"var minItems={self._min_items};"
            f"var maxItems={max_items_js};"
            f"window.{uid}_add=function(){{"
            f"if(maxItems!==null&&container.querySelectorAll('[data-repeater-row]').length>=maxItems)return;"
            f"var clone=tmpl.content.cloneNode(true);"
            f"container.appendChild(clone);"
            f"{uid}_update();"
            f"}};"
            f"window.{uid}_remove=function(btn){{"
            f"var rows=container.querySelectorAll('[data-repeater-row]');"
            f"if(rows.length<=minItems)return;"
            f"btn.closest('[data-repeater-row]').remove();"
            f"{uid}_update();"
            f"}};"
            f"window.{uid}_update=function(){{"
            f"var rows=container.querySelectorAll('[data-repeater-row]');"
            f"var btns=container.querySelectorAll('[data-repeater-remove]');"
            f"btns.forEach(function(b){{b.disabled=rows.length<=minItems;}});"
            f"}};"
            f"{uid}_update();"
            f"}})()</script>"
        )

        attrs = dict(self._attrs)
        attr_str = _render_attrs(attrs)

        return Markup(
            f"<div{attr_str}>"
            f'<div id="{rid}-rows">{rows_html}</div>'
            f'<button type="button" class="btn btn-outline btn-sm mt-1" '
            f'onclick="{uid}_add()">+ {add_label_esc}</button>'
            f'<template id="{rid}-tmpl">{tmpl_html}</template>'
            f"{script}"
            f"</div>"
        )
