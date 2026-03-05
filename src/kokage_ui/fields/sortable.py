"""Drag & Drop sortable list component using SortableJS.

Renders a sortable list with inline <script> for SortableJS configuration.
"""

from __future__ import annotations

import uuid
from typing import Any

from markupsafe import Markup, escape

from kokage_ui.elements import Component


class SortableList(Component):
    """SortableJS-powered drag & drop list with htmx reorder callback.

    Args:
        items: List of dicts with "id", "label", and optional "badge".
        url: POST endpoint to receive reordered IDs.
        list_id: HTML id for the list element (auto-generated if None).
        handle: Show drag handle icon (default True). If False, entire row is draggable.
        ghost_class: CSS class for the drag ghost (default "opacity-50").
        animation: Animation duration in ms (default 150).
        group: SortableJS group name for cross-list dragging.
        **attrs: Additional attributes for the outer div.
    """

    tag = "div"

    def __init__(
        self,
        *,
        items: list[dict[str, Any]],
        url: str,
        list_id: str | None = None,
        handle: bool = True,
        ghost_class: str = "opacity-50",
        animation: int = 150,
        group: str | None = None,
        **attrs: Any,
    ) -> None:
        self._items = items
        self._url = url
        self._list_id = list_id or f"kokage-sortable-{uuid.uuid4().hex[:8]}"
        self._handle = handle
        self._ghost_class = ghost_class
        self._animation = animation
        self._group = group
        self._attrs = attrs

    def render(self) -> str:
        list_id = self._list_id

        # Build list items
        li_parts: list[str] = []
        for item in self._items:
            item_id = escape(str(item["id"]))
            label = escape(str(item.get("label", item["id"])))

            parts: list[str] = []
            if self._handle:
                parts.append(
                    '<span class="sortable-handle cursor-grab mr-2 select-none">'
                    "\u2807</span>"
                )
            parts.append(f"<span>{label}</span>")

            badge = item.get("badge")
            if badge is not None:
                parts.append(
                    f'<span class="badge badge-ghost badge-sm ml-auto">'
                    f"{escape(str(badge))}</span>"
                )

            inner = "".join(parts)
            li_parts.append(
                f'<li data-id="{item_id}" class="flex items-center p-2 '
                f'border rounded mb-1 bg-base-100">{inner}</li>'
            )

        items_html = "".join(li_parts)
        ul_html = f'<ul id="{list_id}" class="list-none p-0">{items_html}</ul>'

        # SortableJS options
        handle_opt = f'handle:".sortable-handle",' if self._handle else ""
        group_opt = f'group:"{escape(self._group)}",' if self._group else ""

        script = (
            f"<script>(function(){{"
            f"if(typeof Sortable==='undefined'){{console.error('SortableJS not loaded');return;}}"
            f"var el=document.getElementById('{list_id}');"
            f"Sortable.create(el,{{"
            f"{handle_opt}"
            f"{group_opt}"
            f'ghostClass:"{escape(self._ghost_class)}",'
            f"animation:{self._animation},"
            f"onEnd:function(){{"
            f"var ids=Array.from(el.children).map(function(li){{return li.dataset.id;}});"
            f"htmx.ajax('POST','{escape(self._url)}',{{values:{{ids:JSON.stringify(ids)}},swap:'none'}});"
            f"}}"
            f"}});"
            f"}})()</script>"
        )

        from kokage_ui.elements import _render_attrs

        attr_str = _render_attrs(self._attrs)

        return Markup(f"<div{attr_str}>{ul_html}{script}</div>")
