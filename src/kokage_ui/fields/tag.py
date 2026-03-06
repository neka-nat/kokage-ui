"""Tag input field for chip-based tag entry.

Provides TagField annotation for Pydantic models and
TagInput component that renders an inline chip/badge UI
with keyboard-driven tag addition and removal.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from markupsafe import Markup, escape

from kokage_ui.elements import Component


@dataclass(frozen=True)
class TagField:
    """Annotated marker for tag input fields.

    Usage:
        class Article(BaseModel):
            tags: Annotated[list[str], TagField()] = []
            categories: Annotated[list[str], TagField(
                placeholder="カテゴリを入力...", color="secondary",
            )] = []
    """

    placeholder: str = "タグを入力..."
    max_tags: int | None = None
    allow_duplicates: bool = False
    separator: str = ","
    color: str = "primary"


class TagInput(Component):
    """Chip-based tag input with inline text entry.

    Renders tags as DaisyUI badges with remove buttons, plus a text
    input for adding new tags via Enter, separator key, or blur.
    Each tag generates a hidden input for form submission.

    Args:
        name: Form field name (shared across all hidden inputs).
        values: Initial list of tag strings.
        placeholder: Placeholder text for the input.
        max_tags: Maximum number of tags (None = unlimited).
        allow_duplicates: Whether duplicate tags are allowed.
        separator: Character that triggers tag addition.
        color: DaisyUI badge color variant.
        input_id: HTML id prefix (auto-generated if None).
    """

    tag = "div"

    def __init__(
        self,
        *,
        name: str = "",
        values: list[str] | None = None,
        placeholder: str = "タグを入力...",
        max_tags: int | None = None,
        allow_duplicates: bool = False,
        separator: str = ",",
        color: str = "primary",
        input_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self._name = name
        self._values = values or []
        self._placeholder = placeholder
        self._max_tags = max_tags
        self._allow_duplicates = allow_duplicates
        self._separator = separator
        self._color = color
        self._input_id = input_id or f"kokage-tag-{uuid.uuid4().hex[:8]}"
        self._attrs = attrs

    def render(self) -> str:
        from kokage_ui.elements import _render_attrs

        tid = self._input_id
        uid = tid.replace("-", "_")
        name_esc = escape(self._name)
        placeholder_esc = escape(self._placeholder)
        color_esc = escape(self._color)
        separator_esc = escape(self._separator)
        max_tags_js = "null" if self._max_tags is None else str(self._max_tags)
        allow_dup_js = "true" if self._allow_duplicates else "false"

        # Build existing tag chips + hidden inputs
        tags_html_parts: list[str] = []
        for val in self._values:
            val_esc = escape(str(val))
            tags_html_parts.append(
                f'<span class="badge badge-{color_esc} gap-1" data-tag-chip>'
                f'{val_esc}'
                f'<button type="button" class="btn btn-ghost btn-xs p-0 min-h-0 h-auto" '
                f'onclick="{uid}_remove(this)">\u2715</button>'
                f'</span>'
                f'<input type="hidden" name="{name_esc}" value="{val_esc}" data-tag-hidden />'
            )
        tags_html = "".join(tags_html_parts)

        script = (
            f"<script>(function(){{"
            f"var container=document.getElementById('{tid}-tags');"
            f"var input=document.getElementById('{tid}-input');"
            f"var maxTags={max_tags_js};"
            f"var allowDup={allow_dup_js};"
            f"var sep='{separator_esc}';"
            f"window.{uid}_add=function(text){{"
            f"text=text.trim();"
            f"if(!text)return;"
            f"if(maxTags!==null&&container.querySelectorAll('[data-tag-chip]').length>=maxTags)return;"
            f"if(!allowDup){{"
            f"var existing=container.querySelectorAll('[data-tag-hidden]');"
            f"for(var i=0;i<existing.length;i++){{if(existing[i].value===text)return;}}"
            f"}}"
            f"var span=document.createElement('span');"
            f"span.className='badge badge-{color_esc} gap-1';"
            f"span.setAttribute('data-tag-chip','');"
            f"span.textContent=text;"
            f"var btn=document.createElement('button');"
            f"btn.type='button';"
            f"btn.className='btn btn-ghost btn-xs p-0 min-h-0 h-auto';"
            f"btn.textContent='\\u2715';"
            f"btn.onclick=function(){{ {uid}_remove(btn); }};"
            f"span.appendChild(btn);"
            f"var hidden=document.createElement('input');"
            f"hidden.type='hidden';"
            f"hidden.name='{name_esc}';"
            f"hidden.value=text;"
            f"hidden.setAttribute('data-tag-hidden','');"
            f"container.insertBefore(span,input);"
            f"container.insertBefore(hidden,input);"
            f"input.value='';"
            f"}};"
            f"window.{uid}_remove=function(btn){{"
            f"var chip=btn.closest('[data-tag-chip]');"
            f"var hidden=chip.nextElementSibling;"
            f"if(hidden&&hidden.hasAttribute('data-tag-hidden'))hidden.remove();"
            f"chip.remove();"
            f"}};"
            f"input.addEventListener('keydown',function(e){{"
            f"if(e.key==='Enter'||e.key===sep){{"
            f"e.preventDefault();"
            f"{uid}_add(input.value);"
            f"}}else if(e.key==='Backspace'&&input.value===''){{"
            f"var chips=container.querySelectorAll('[data-tag-chip]');"
            f"if(chips.length>0){{"
            f"var last=chips[chips.length-1];"
            f"var hidden=last.nextElementSibling;"
            f"if(hidden&&hidden.hasAttribute('data-tag-hidden'))hidden.remove();"
            f"last.remove();"
            f"}}"
            f"}}"
            f"}});"
            f"input.addEventListener('blur',function(){{"
            f"{uid}_add(input.value);"
            f"}});"
            f"}})()</script>"
        )

        attrs = dict(self._attrs)
        attr_str = _render_attrs(attrs)

        return Markup(
            f"<div{attr_str}>"
            f'<div id="{tid}-tags" class="flex flex-wrap gap-1 items-center p-2 '
            f'border rounded-lg min-h-[2.5rem] cursor-text">'
            f"{tags_html}"
            f'<input type="text" id="{tid}-input" placeholder="{placeholder_esc}" '
            f'class="outline-none bg-transparent flex-1 min-w-[80px] text-sm" />'
            f"</div>"
            f"{script}"
            f"</div>"
        )
