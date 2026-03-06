"""Date/time picker component using flatpickr.

Provides DateField, TimeField, DateTimeField annotations for Pydantic models
and DateTimePicker component that renders a flatpickr-based date/time picker.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from markupsafe import Markup, escape

from kokage_ui.elements import Component


@dataclass(frozen=True)
class DateField:
    """Annotated marker for date fields.

    Usage:
        class Event(BaseModel):
            date: Annotated[str, DateField()] = ""
    """

    format: str = "Y-m-d"
    min_date: str | None = None
    max_date: str | None = None
    placeholder: str = ""


@dataclass(frozen=True)
class TimeField:
    """Annotated marker for time fields.

    Usage:
        class Event(BaseModel):
            start_time: Annotated[str, TimeField()] = ""
    """

    format: str = "H:i"
    enable_seconds: bool = False
    time_24hr: bool = True
    placeholder: str = ""


@dataclass(frozen=True)
class DateTimeField:
    """Annotated marker for datetime fields.

    Usage:
        class Event(BaseModel):
            starts_at: Annotated[str, DateTimeField()] = ""
    """

    format: str = "Y-m-d H:i"
    enable_time: bool = True
    time_24hr: bool = True
    min_date: str | None = None
    max_date: str | None = None
    placeholder: str = ""


class DateTimePicker(Component):
    """Flatpickr date/time picker component.

    Renders an input with flatpickr initialization script.

    Args:
        name: Form field name.
        value: Initial value.
        field_config: DateField, TimeField, or DateTimeField instance.
        picker_id: HTML id (auto-generated if None).
    """

    tag = "div"

    def __init__(
        self,
        *,
        name: str = "",
        value: str = "",
        field_config: DateField | TimeField | DateTimeField | None = None,
        picker_id: str | None = None,
        **attrs: Any,
    ) -> None:
        self._name = name
        self._value = value
        self._field_config = field_config or DateField()
        self._picker_id = picker_id or f"kokage-fp-{uuid.uuid4().hex[:8]}"
        self._attrs = attrs

    def render(self) -> str:
        from kokage_ui.elements import _render_attrs

        cfg = self._field_config
        pid = self._picker_id
        escaped_value = escape(self._value)

        # Build flatpickr options
        options: dict[str, Any] = {"dateFormat": cfg.format}

        if isinstance(cfg, TimeField):
            options["enableTime"] = True
            options["noCalendar"] = True
            options["time_24hr"] = cfg.time_24hr
            options["dateFormat"] = cfg.format
            if cfg.enable_seconds:
                options["enableSeconds"] = True
        elif isinstance(cfg, DateTimeField):
            options["enableTime"] = cfg.enable_time
            options["time_24hr"] = cfg.time_24hr
            if cfg.min_date:
                options["minDate"] = cfg.min_date
            if cfg.max_date:
                options["maxDate"] = cfg.max_date
        elif isinstance(cfg, DateField):
            if cfg.min_date:
                options["minDate"] = cfg.min_date
            if cfg.max_date:
                options["maxDate"] = cfg.max_date

        placeholder = ""
        if hasattr(cfg, "placeholder"):
            placeholder = cfg.placeholder

        options_json = json.dumps(options, ensure_ascii=False, separators=(",", ":"))

        # Build input attributes
        input_attrs: dict[str, Any] = {}
        input_attrs.update(self._attrs)
        attr_str = _render_attrs(input_attrs)

        script = (
            f"<script>(function(){{"
            f"if(typeof flatpickr==='undefined'){{console.error('flatpickr not loaded');return;}}"
            f"flatpickr('#{pid}',{options_json});"
            f"}})()</script>"
        )

        return Markup(
            f"<div{attr_str}>"
            f'<input type="text" id="{pid}" name="{escape(self._name)}" '
            f'value="{escaped_value}" placeholder="{escape(placeholder)}" '
            f'class="input input-bordered w-full" />'
            f"{script}"
            f"</div>"
        )
