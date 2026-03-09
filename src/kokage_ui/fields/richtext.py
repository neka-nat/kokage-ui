"""Rich text editor component using Quill.

Provides RichTextField annotation for Pydantic models and
RichTextEditor component that renders a Quill editor with
hidden input synchronization for form submission.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from pydantic.dataclasses import dataclass as pydantic_dataclass

from markupsafe import Markup, escape

from kokage_ui.elements import Component

_TOOLBAR_PRESETS: dict[str, list[Any]] = {
    "minimal": [["bold", "italic", "link"]],
    "standard": [
        [{"header": [1, 2, 3, False]}],
        ["bold", "italic", "underline"],
        [{"list": "ordered"}, {"list": "bullet"}],
        ["link", "image", "code-block"],
        ["clean"],
    ],
    "full": [
        [{"header": [1, 2, 3, 4, 5, 6, False]}],
        ["bold", "italic", "underline", "strike"],
        [{"color": []}, {"background": []}],
        [{"list": "ordered"}, {"list": "bullet"}, {"indent": "-1"}, {"indent": "+1"}],
        [{"align": []}],
        ["link", "image", "video", "code-block", "blockquote"],
        ["clean"],
    ],
}


@pydantic_dataclass(frozen=True)
class RichTextField:
    """Annotated marker for rich text fields.

    Usage:
        class Article(BaseModel):
            body: Annotated[str, RichTextField()] = ""
            summary: Annotated[str, RichTextField(height="200px", toolbar="minimal")] = ""
    """

    height: str = "300px"
    placeholder: str = ""
    toolbar: str = "standard"  # "standard" | "minimal" | "full"


class RichTextEditor(Component):
    """Quill rich text editor.

    Renders a Quill editor with a hidden input that syncs the HTML content
    for form submission. Works with both standard form submit and htmx.

    Args:
        name: Form field name (hidden input).
        value: Initial HTML content.
        height: Editor height CSS (default "300px").
        placeholder: Placeholder text.
        toolbar: Toolbar preset ("minimal", "standard", "full").
        editor_id: HTML id (auto-generated if None).
    """

    tag = "div"

    def __init__(
        self,
        *,
        name: str = "",
        value: str = "",
        height: str = "300px",
        placeholder: str = "",
        toolbar: str = "standard",
        editor_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self._name = name
        self._value = value
        self._height = height
        self._placeholder = placeholder
        self._toolbar = toolbar
        self._editor_id = editor_id or f"kokage-rte-{uuid.uuid4().hex[:8]}"
        self._attrs = attrs

    def render(self) -> str:
        from kokage_ui.elements import _render_attrs

        eid = self._editor_id
        hidden_id = f"{eid}-input"
        escaped_value = escape(self._value)
        toolbar_config = json.dumps(
            _TOOLBAR_PRESETS.get(self._toolbar, _TOOLBAR_PRESETS["standard"]),
            ensure_ascii=False,
        )
        placeholder_js = json.dumps(self._placeholder, ensure_ascii=False)

        attrs = dict(self._attrs)
        attr_str = _render_attrs(attrs)

        script = (
            f"<script>(function(){{"
            f"if(typeof Quill==='undefined'){{console.error('Quill is not loaded');return;}}"
            f"var q=new Quill('#{eid}',{{theme:'snow',placeholder:{placeholder_js},"
            f"modules:{{toolbar:{toolbar_config}}}}});"
            f"var hidden=document.getElementById('{hidden_id}');"
            f"hidden.value=q.root.innerHTML;"
            f"q.on('text-change',function(){{hidden.value=q.root.innerHTML;}});"
            f"var form=hidden.closest('form');"
            f"if(form){{form.addEventListener('submit',function(){{hidden.value=q.root.innerHTML;}});}}"
            f"document.body.addEventListener('htmx:configRequest',function(e){{"
            f"if(e.detail.elt.closest&&e.detail.elt.closest('form')){{"
            f"hidden.value=q.root.innerHTML;}}}});"
            f"}})()</script>"
        )

        return Markup(
            f"<div{attr_str}>"
            f'<div id="{eid}" style="height:{escape(self._height)}">{escaped_value}</div>'
            f'<input type="hidden" name="{escape(self._name)}" '
            f'id="{hidden_id}" value="{escaped_value}" />'
            f"{script}"
            f"</div>"
        )
