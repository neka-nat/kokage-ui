"""Pydantic model to UI auto-generation.

Automatically generates DaisyUI-styled forms, tables, and detail views
from Pydantic BaseModel definitions.
"""

from __future__ import annotations

import enum
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from kokage_ui.components import Alert, Badge, Card, DaisyTable
from kokage_ui.elements import (
    Button,
    Component,
    Div,
    Input,
    Label,
    Option,
    Select,
    Span,
    Strong,
    Textarea,
)

_SENTINEL = object()

# Heuristic field name patterns
_TEXTAREA_NAME_HINTS = {"bio", "description", "about", "summary", "note", "notes", "comment", "comments", "content", "body", "message", "text"}
_EMAIL_NAME_HINTS = {"email", "email_address", "mail"}
_PASSWORD_NAME_HINTS = {"password", "passwd", "pass", "secret"}

_TEXTAREA_MAX_LENGTH_THRESHOLD = 200


def _resolve_annotation(annotation: Any) -> tuple[Any, bool]:
    """Resolve a type annotation to (base_type, is_optional).

    Handles Optional[X], X | None, Literal, and plain types.
    """
    origin = get_origin(annotation)

    # Handle Union types: Optional[X] is Union[X, None]
    if origin is Union or isinstance(annotation, types.UnionType):
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0], True
        # Multi-type union (not just Optional) — return as-is
        return annotation, False

    # Literal stays as-is
    if origin is Literal:
        return annotation, False

    return annotation, False


@dataclass
class FieldConstraints:
    """Extracted constraints from Pydantic field metadata."""

    min_length: int | None = None
    max_length: int | None = None
    gt: int | float | None = None
    ge: int | float | None = None
    lt: int | float | None = None
    le: int | float | None = None
    pattern: str | None = None


def _extract_constraints(field_info: FieldInfo) -> FieldConstraints:
    """Extract validation constraints from Pydantic FieldInfo metadata."""
    c = FieldConstraints()
    for m in field_info.metadata:
        cls_name = type(m).__name__
        if cls_name == "MinLen":
            c.min_length = m.min_length
        elif cls_name == "MaxLen":
            c.max_length = m.max_length
        elif cls_name == "Gt":
            c.gt = m.gt
        elif cls_name == "Ge":
            c.ge = m.ge
        elif cls_name == "Lt":
            c.lt = m.lt
        elif cls_name == "Le":
            c.le = m.le
        elif hasattr(m, "pattern"):
            c.pattern = m.pattern
    return c


def _build_form_input(
    *,
    label_text: str,
    input_element: Component,
    error_message: str | None = None,
) -> Component:
    """Build a DaisyUI-styled form-control wrapping an input element."""
    children: list[Any] = []
    children.append(
        Label(Span(label_text, cls="label-text"), cls="label")
    )
    children.append(input_element)
    if error_message:
        children.append(Span(error_message, cls="text-error text-sm mt-1"))
    return Div(*children, cls="form-control w-full")


def _field_to_component(
    name: str,
    field_info: FieldInfo,
    *,
    value: Any = _SENTINEL,
    error_message: str | None = None,
) -> Component:
    """Convert a single Pydantic field to a form input component.

    Args:
        name: Field name.
        field_info: Pydantic FieldInfo.
        value: Pre-fill value (_SENTINEL means use default).
        error_message: Inline error message to display.
    """
    base_type, is_optional = _resolve_annotation(field_info.annotation)
    constraints = _extract_constraints(field_info)
    label_text = field_info.title or name.replace("_", " ").title()
    is_required = field_info.is_required() and not is_optional

    # Common HTML attributes
    common_attrs: dict[str, Any] = {"name": name}
    if is_required:
        common_attrs["required"] = True

    error_cls_suffix = " input-error" if error_message else ""

    # --- bool → checkbox ---
    if base_type is bool:
        if value is not _SENTINEL:
            checked = bool(value)
        elif field_info.default is not None and field_info.default is not PydanticUndefined:
            checked = bool(field_info.default)
        else:
            checked = False
        input_el = Input(
            type="checkbox",
            cls="checkbox",
            checked=checked if checked else False,
            **common_attrs,
        )
        children: list[Any] = [
            Label(
                input_el,
                Span(label_text, cls="label-text ml-2"),
                cls="label cursor-pointer justify-start gap-2",
            ),
        ]
        if error_message:
            children.append(Span(error_message, cls="text-error text-sm mt-1"))
        return Div(*children, cls="form-control w-full")

    # --- Literal → select ---
    origin = get_origin(base_type)
    if origin is Literal:
        choices = get_args(base_type)
        if value is not _SENTINEL:
            selected_val = value
        else:
            selected_val = field_info.default if field_info.default is not PydanticUndefined else None
        options = []
        for choice in choices:
            opt_attrs: dict[str, Any] = {"value": str(choice)}
            if selected_val is not None and str(choice) == str(selected_val):
                opt_attrs["selected"] = True
            options.append(Option(str(choice), **opt_attrs))
        select_el = Select(
            *options,
            cls=f"select select-bordered w-full{error_cls_suffix}",
            **common_attrs,
        )
        return _build_form_input(label_text=label_text, input_element=select_el, error_message=error_message)

    # --- Enum → select ---
    if isinstance(base_type, type) and issubclass(base_type, enum.Enum):
        if value is not _SENTINEL:
            selected_val = value
        else:
            selected_val = field_info.default if field_info.default is not PydanticUndefined else None
        options = []
        for member in base_type:
            opt_attrs = {"value": member.value}
            if selected_val is not None and (member == selected_val or member.value == selected_val):
                opt_attrs["selected"] = True
            options.append(Option(member.name, **opt_attrs))
        select_el = Select(
            *options,
            cls=f"select select-bordered w-full{error_cls_suffix}",
            **common_attrs,
        )
        return _build_form_input(label_text=label_text, input_element=select_el, error_message=error_message)

    # --- int → number input (step=1) ---
    if base_type is int:
        input_attrs = _numeric_attrs(constraints, step="1")
        input_attrs.update(common_attrs)
        _apply_value_or_default(input_attrs, value, field_info)
        input_el = Input(
            type="number",
            cls=f"input input-bordered w-full{error_cls_suffix}",
            **input_attrs,
        )
        return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message)

    # --- float → number input (step=any) ---
    if base_type is float:
        input_attrs = _numeric_attrs(constraints, step="any")
        input_attrs.update(common_attrs)
        _apply_value_or_default(input_attrs, value, field_info)
        input_el = Input(
            type="number",
            cls=f"input input-bordered w-full{error_cls_suffix}",
            **input_attrs,
        )
        return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message)

    # --- str (with heuristics) ---
    if base_type is str:
        name_lower = name.lower()

        # email heuristic
        if name_lower in _EMAIL_NAME_HINTS:
            input_attrs = _string_attrs(constraints)
            input_attrs.update(common_attrs)
            _apply_value_or_default(input_attrs, value, field_info)
            input_el = Input(
                type="email",
                cls=f"input input-bordered w-full{error_cls_suffix}",
                **input_attrs,
            )
            return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message)

        # password heuristic
        if name_lower in _PASSWORD_NAME_HINTS:
            input_attrs = _string_attrs(constraints)
            input_attrs.update(common_attrs)
            _apply_value_or_default(input_attrs, value, field_info)
            input_el = Input(
                type="password",
                cls=f"input input-bordered w-full{error_cls_suffix}",
                **input_attrs,
            )
            return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message)

        # textarea heuristic: long max_length or name hint
        is_textarea = (
            name_lower in _TEXTAREA_NAME_HINTS
            or (constraints.max_length is not None and constraints.max_length > _TEXTAREA_MAX_LENGTH_THRESHOLD)
        )
        if is_textarea:
            ta_attrs: dict[str, Any] = {}
            if constraints.min_length is not None:
                ta_attrs["minlength"] = str(constraints.min_length)
            if constraints.max_length is not None:
                ta_attrs["maxlength"] = str(constraints.max_length)
            ta_attrs.update(common_attrs)
            ta_attrs["rows"] = "3"
            ta_children: list[Any] = []
            if value is not _SENTINEL:
                ta_children.append(str(value))
            else:
                default = field_info.default
                if default is not None and default is not PydanticUndefined:
                    ta_children.append(str(default))
            ta_cls = f"textarea textarea-bordered w-full{' textarea-error' if error_message else ''}"
            ta_el = Textarea(*ta_children, cls=ta_cls, **ta_attrs)
            return _build_form_input(label_text=label_text, input_element=ta_el, error_message=error_message)

        # fallback: text input
        input_attrs = _string_attrs(constraints)
        input_attrs.update(common_attrs)
        _apply_value_or_default(input_attrs, value, field_info)
        input_el = Input(
            type="text",
            cls=f"input input-bordered w-full{error_cls_suffix}",
            **input_attrs,
        )
        return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message)

    # --- fallback for unknown types → text input ---
    input_attrs = _string_attrs(constraints)
    input_attrs.update(common_attrs)
    _apply_value_or_default(input_attrs, value, field_info)
    input_el = Input(
        type="text",
        cls=f"input input-bordered w-full{error_cls_suffix}",
        **input_attrs,
    )
    return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message)


def _numeric_attrs(constraints: FieldConstraints, step: str) -> dict[str, Any]:
    """Build HTML attributes for numeric inputs."""
    attrs: dict[str, Any] = {"step": step}
    if constraints.ge is not None:
        attrs["min"] = str(constraints.ge)
    elif constraints.gt is not None:
        attrs["min"] = str(constraints.gt)
    if constraints.le is not None:
        attrs["max"] = str(constraints.le)
    elif constraints.lt is not None:
        attrs["max"] = str(constraints.lt)
    return attrs


def _string_attrs(constraints: FieldConstraints) -> dict[str, Any]:
    """Build HTML attributes for string inputs."""
    attrs: dict[str, Any] = {}
    if constraints.min_length is not None:
        attrs["minlength"] = str(constraints.min_length)
    if constraints.max_length is not None:
        attrs["maxlength"] = str(constraints.max_length)
    if constraints.pattern is not None:
        attrs["pattern"] = constraints.pattern
    return attrs


def _apply_default(attrs: dict[str, Any], field_info: FieldInfo) -> None:
    """Apply default value to input attrs if present."""
    default = field_info.default
    if default is not None and default is not PydanticUndefined:
        attrs["value"] = str(default)


def _apply_value_or_default(
    attrs: dict[str, Any], value: Any, field_info: FieldInfo
) -> None:
    """Apply explicit value or fall back to field default."""
    if value is not _SENTINEL:
        attrs["value"] = str(value)
    else:
        _apply_default(attrs, field_info)


def _filter_fields(
    model: type[BaseModel],
    include: set[str] | list[str] | None,
    exclude: set[str] | list[str] | None,
) -> list[tuple[str, FieldInfo]]:
    """Filter model fields by include/exclude sets."""
    include_set = set(include) if include else None
    exclude_set = set(exclude) if exclude else set()
    result = []
    for name, field_info in model.model_fields.items():
        if include_set is not None and name not in include_set:
            continue
        if name in exclude_set:
            continue
        result.append((name, field_info))
    return result


class ModelForm(Component):
    """Auto-generate a DaisyUI-styled form from a Pydantic model.

    Args:
        model: Pydantic BaseModel class.
        action: Form action URL.
        method: Form HTTP method.
        submit_text: Text for the submit button.
        submit_color: DaisyUI color for the submit button.
        exclude: Field names to exclude.
        include: Field names to include (if set, only these are shown).
        instance: Model instance to pre-fill the form (edit mode).
        values: Dict of field values to restore (validation failure).
        errors: List of Pydantic ValidationError dicts for inline errors.
    """

    tag = "form"

    def __init__(
        self,
        model: type[BaseModel],
        *,
        action: str = "",
        method: str = "post",
        submit_text: str = "Submit",
        submit_color: str = "primary",
        exclude: set[str] | list[str] | None = None,
        include: set[str] | list[str] | None = None,
        instance: BaseModel | None = None,
        values: dict[str, Any] | None = None,
        errors: list[dict[str, Any]] | None = None,
        **attrs: Any,
    ) -> None:
        fields = _filter_fields(model, include, exclude)

        # Build error lookup: field_name → first error message
        error_map: dict[str, str] = {}
        if errors:
            for err in errors:
                loc = err.get("loc", ())
                if loc:
                    field_name = str(loc[0])
                    if field_name not in error_map:
                        error_map[field_name] = err.get("msg", "Invalid value")

        children: list[Any] = []

        # Show alert when errors exist
        if errors:
            children.append(Alert("Please fix the errors below.", variant="error"))

        for name, field_info in fields:
            # Determine value: values dict takes priority, then instance
            if values is not None and name in values:
                val = values[name]
            elif instance is not None:
                val = getattr(instance, name)
            else:
                val = _SENTINEL

            children.append(
                _field_to_component(
                    name,
                    field_info,
                    value=val,
                    error_message=error_map.get(name),
                )
            )

        # Submit button
        btn_cls = f"btn btn-{submit_color} mt-4"
        children.append(Button(submit_text, type="submit", cls=btn_cls))

        attrs["action"] = action
        attrs["method"] = method
        super().__init__(*children, **attrs)


def _render_value(value: Any) -> Any:
    """Render a field value for display in table/detail views."""
    if isinstance(value, bool):
        if value:
            return Badge("Active", color="success")
        return Badge("Inactive", color="error")
    if isinstance(value, enum.Enum):
        return str(value.value)
    if value is None:
        return "-"
    return str(value)


class ModelTable(Component):
    """Auto-generate a DaisyUI-styled table from a Pydantic model + rows.

    Args:
        model: Pydantic BaseModel class.
        rows: List of model instances.
        exclude: Field names to exclude.
        include: Field names to include.
        zebra: Use zebra striping.
        compact: Use compact size.
        cell_renderers: Dict of field_name → callable(value) for custom rendering.
    """

    tag = "div"

    def __init__(
        self,
        model: type[BaseModel],
        *,
        rows: list[BaseModel],
        exclude: set[str] | list[str] | None = None,
        include: set[str] | list[str] | None = None,
        zebra: bool = False,
        compact: bool = False,
        cell_renderers: dict[str, Callable[[Any], Any]] | None = None,
        extra_columns: dict[str, Callable[[BaseModel], Any]] | None = None,
        **attrs: Any,
    ) -> None:
        fields = _filter_fields(model, include, exclude)
        cell_renderers = cell_renderers or {}
        extra_columns = extra_columns or {}

        headers = [
            fi.title or name.replace("_", " ").title()
            for name, fi in fields
        ]
        headers.extend(extra_columns.keys())

        table_rows = []
        for row in rows:
            cells = []
            for name, _fi in fields:
                value = getattr(row, name)
                if name in cell_renderers:
                    cells.append(cell_renderers[name](value))
                else:
                    cells.append(_render_value(value))
            for renderer in extra_columns.values():
                cells.append(renderer(row))
            table_rows.append(cells)

        table = DaisyTable(
            headers=headers,
            rows=table_rows,
            zebra=zebra,
            compact=compact,
        )

        super().__init__(table, **attrs)


class ModelDetail(Component):
    """Auto-generate a DaisyUI-styled detail view from a Pydantic model instance.

    Args:
        instance: Pydantic model instance.
        exclude: Field names to exclude.
        include: Field names to include.
        title: Card title (defaults to model class name).
    """

    tag = "div"

    def __init__(
        self,
        instance: BaseModel,
        *,
        exclude: set[str] | list[str] | None = None,
        include: set[str] | list[str] | None = None,
        title: str | None = None,
        **attrs: Any,
    ) -> None:
        model = type(instance)
        fields = _filter_fields(model, include, exclude)

        card_title = title or model.__name__

        rows: list[Any] = []
        for name, fi in fields:
            label_text = fi.title or name.replace("_", " ").title()
            value = getattr(instance, name)
            rendered = _render_value(value)
            rows.append(
                Div(
                    Strong(label_text, cls="text-sm opacity-70"),
                    Div(rendered, cls="text-lg"),
                    cls="py-2",
                )
            )

        card = Card(*rows, title=card_title)
        super().__init__(card, **attrs)
