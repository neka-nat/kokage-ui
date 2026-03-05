"""Pydantic model to UI auto-generation.

Automatically generates DaisyUI-styled forms, tables, and detail views
from Pydantic BaseModel definitions.
"""

from __future__ import annotations

import enum
import types
from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from kokage_ui.components import Alert, Badge, Card, DaisyTable
from kokage_ui.elements import (
    A,
    Audio,
    Button,
    Component,
    Div,
    Img,
    Input,
    Label,
    Option,
    Select,
    Source,
    Span,
    Strong,
    Tbody,
    Td,
    Textarea,
    Th,
    Thead,
    Tr,
    Video,
)
from kokage_ui.media import MediaField
from kokage_ui.repeater import RepeaterField, RepeaterInput
from kokage_ui.richtext import RichTextField, RichTextEditor

_SENTINEL = object()

# Heuristic field name patterns
_TEXTAREA_NAME_HINTS = {"bio", "description", "about", "summary", "note", "notes", "comment", "comments", "content", "body", "message", "text"}
_EMAIL_NAME_HINTS = {"email", "email_address", "mail"}
_PASSWORD_NAME_HINTS = {"password", "passwd", "pass", "secret"}

_TEXTAREA_MAX_LENGTH_THRESHOLD = 200


def _resolve_annotation(annotation: Any) -> tuple[Any, bool]:
    """Resolve a type annotation to (base_type, is_optional).

    Handles Annotated[X, ...], Optional[X], X | None, Literal, and plain types.
    """
    origin = get_origin(annotation)

    # Handle Annotated[X, ...] → unwrap to X
    if origin is Annotated:
        args = get_args(annotation)
        if args:
            return _resolve_annotation(args[0])
        return annotation, False

    # Handle Union types: Optional[X] is Union[X, None]
    if origin is Union or isinstance(annotation, types.UnionType):
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            base, _ = _resolve_annotation(non_none[0])
            return base, True
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
    field_id: str | None = None,
) -> Component:
    """Build a DaisyUI-styled form-control wrapping an input element."""
    children: list[Any] = []
    children.append(
        Label(Span(label_text, cls="label-text"), cls="label")
    )
    children.append(input_element)
    if error_message:
        children.append(Span(error_message, cls="text-error text-sm mt-1"))
    wrapper_attrs: dict[str, Any] = {"cls": "form-control w-full"}
    if field_id:
        wrapper_attrs["id"] = field_id
    return Div(*children, **wrapper_attrs)


def _extract_media_field(field_info: FieldInfo) -> MediaField | None:
    """Extract MediaField from Pydantic field metadata."""
    for m in field_info.metadata:
        if isinstance(m, MediaField):
            return m
    return None


def _extract_rich_text_field(field_info: FieldInfo) -> RichTextField | None:
    """Extract RichTextField from Pydantic field metadata."""
    for m in field_info.metadata:
        if isinstance(m, RichTextField):
            return m
    return None


def _extract_repeater_field(field_info: FieldInfo) -> RepeaterField | None:
    """Extract RepeaterField from Pydantic field metadata."""
    for m in field_info.metadata:
        if isinstance(m, RepeaterField):
            return m
    return None


def _field_to_component(
    name: str,
    field_info: FieldInfo,
    *,
    value: Any = _SENTINEL,
    error_message: str | None = None,
    extra_input_attrs: dict[str, Any] | None = None,
    field_id: str | None = None,
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
    if extra_input_attrs:
        common_attrs.update(extra_input_attrs)

    error_cls_suffix = " input-error" if error_message else ""

    # --- RichTextField → Quill editor ---
    rich = _extract_rich_text_field(field_info)
    if rich is not None:
        editor_value = ""
        if value is not _SENTINEL and value:
            editor_value = str(value)
        editor = RichTextEditor(
            name=name,
            value=editor_value,
            height=rich.height,
            placeholder=rich.placeholder,
            toolbar=rich.toolbar,
        )
        return _build_form_input(
            label_text=label_text,
            input_element=editor,
            error_message=error_message,
            field_id=field_id,
        )

    # --- MediaField → file input with preview ---
    media = _extract_media_field(field_info)
    if media is not None:
        input_el = Input(
            type="file",
            accept=media.accept_str,
            cls=f"file-input file-input-bordered w-full{error_cls_suffix}",
            **common_attrs,
        )
        children: list[Any] = []
        if value is not _SENTINEL and value:
            if media.media_type == "image":
                preview = Img(src=str(value), cls="max-h-32 rounded mb-2", alt=label_text)
            elif media.media_type == "video":
                preview = Video(Source(src=str(value)), controls=True, cls="max-h-32 rounded mb-2")
            elif media.media_type == "audio":
                preview = Audio(Source(src=str(value)), controls=True, cls="w-full mb-2")
            else:
                preview = None
            if preview:
                children.append(preview)
        children.append(input_el)
        wrapper = Div(*children)
        return _build_form_input(label_text=label_text, input_element=wrapper, error_message=error_message, field_id=field_id)

    # --- RepeaterField → dynamic add/remove rows ---
    repeater = _extract_repeater_field(field_info)
    if repeater is not None:
        items: list[str] = []
        if value is not _SENTINEL and isinstance(value, list):
            items = [str(v) for v in value]
        return _build_form_input(
            label_text=label_text,
            input_element=RepeaterInput(
                name=name,
                values=items,
                min_items=repeater.min_items,
                max_items=repeater.max_items,
                placeholder=repeater.placeholder,
                add_label=repeater.add_label,
            ),
            error_message=error_message,
            field_id=field_id,
        )

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
        bool_attrs: dict[str, Any] = {"cls": "form-control w-full"}
        if field_id:
            bool_attrs["id"] = field_id
        return Div(*children, **bool_attrs)

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
        return _build_form_input(label_text=label_text, input_element=select_el, error_message=error_message, field_id=field_id)

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
        return _build_form_input(label_text=label_text, input_element=select_el, error_message=error_message, field_id=field_id)

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
        return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message, field_id=field_id)

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
        return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message, field_id=field_id)

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
            return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message, field_id=field_id)

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
            return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message, field_id=field_id)

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
            return _build_form_input(label_text=label_text, input_element=ta_el, error_message=error_message, field_id=field_id)

        # fallback: text input
        input_attrs = _string_attrs(constraints)
        input_attrs.update(common_attrs)
        _apply_value_or_default(input_attrs, value, field_info)
        input_el = Input(
            type="text",
            cls=f"input input-bordered w-full{error_cls_suffix}",
            **input_attrs,
        )
        return _build_form_input(label_text=label_text, input_element=input_el, error_message=error_message, field_id=field_id)

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

        # Auto-detect media fields → set enctype
        has_media = any(
            _extract_media_field(fi) is not None
            for _, fi in fields
        )
        if has_media:
            attrs.setdefault("enctype", "multipart/form-data")

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

            field_attrs = self._build_field_attrs(name)
            extra = field_attrs if field_attrs else None
            fid = f"field-{name}" if field_attrs else None

            children.append(
                _field_to_component(
                    name,
                    field_info,
                    value=val,
                    error_message=error_map.get(name),
                    extra_input_attrs=extra,
                    field_id=fid,
                )
            )

        # Submit button
        btn_cls = f"btn btn-{submit_color} mt-4"
        children.append(Button(submit_text, type="submit", cls=btn_cls))

        attrs["action"] = action
        attrs["method"] = method
        super().__init__(*children, **attrs)

    def _build_field_attrs(self, name: str) -> dict[str, Any] | None:
        """Build extra input attributes for a field. Override in subclasses."""
        return None


class ValidatedModelForm(ModelForm):
    """ModelForm with per-field htmx real-time validation.

    Each field gets htmx attributes to POST to a validation endpoint
    on change, receiving back the field wrapper with error/success styling.

    Args:
        model: Pydantic BaseModel class.
        validate_url: Base URL for validation (e.g., "/validate").
        validate_trigger: htmx trigger event (default: "change").
        validate_delay: Debounce delay in ms (default: 500).
        **kwargs: All other ModelForm arguments.
    """

    def __init__(
        self,
        model: type[BaseModel],
        *,
        validate_url: str,
        validate_trigger: str = "change",
        validate_delay: int = 500,
        **kwargs: Any,
    ) -> None:
        self._validate_url = validate_url.rstrip("/")
        self._validate_trigger = validate_trigger
        self._validate_delay = validate_delay
        super().__init__(model, **kwargs)

    def _build_field_attrs(self, name: str) -> dict[str, Any] | None:
        trigger = self._validate_trigger
        if self._validate_delay > 0:
            trigger = f"{trigger} delay:{self._validate_delay}ms"
        return {
            "hx_post": f"{self._validate_url}/{name}",
            "hx_trigger": trigger,
            "hx_target": f"#field-{name}",
            "hx_swap": "outerHTML",
        }


def _render_value(
    value: Any,
    *,
    media_field: MediaField | None = None,
    rich_text_field: RichTextField | None = None,
) -> Any:
    """Render a field value for display in table/detail views."""
    if isinstance(value, bool):
        if value:
            return Badge("Active", color="success")
        return Badge("Inactive", color="error")
    if isinstance(value, list):
        if not value:
            return "-"
        badges = [Badge(str(v), color="ghost") for v in value[:5]]
        if len(value) > 5:
            badges.append(Span(f"+{len(value) - 5}", cls="text-sm opacity-60"))
        return Div(*badges, cls="flex flex-wrap gap-1")
    if isinstance(value, enum.Enum):
        return str(value.value)
    if value is None:
        return "-"
    if rich_text_field and value:
        from kokage_ui.elements import Raw

        safe_html = str(value)[:200]
        return Div(Raw(safe_html), cls="prose prose-sm max-w-xs line-clamp-2")
    if media_field and value:
        if media_field.media_type == "image":
            return Img(src=str(value), cls="max-h-16 rounded", alt="")
        elif media_field.media_type == "video":
            return Badge("Video", color="info")
        elif media_field.media_type == "audio":
            return Badge("Audio", color="info")
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
            for name, fi in fields:
                value = getattr(row, name)
                if name in cell_renderers:
                    cells.append(cell_renderers[name](value))
                else:
                    media = _extract_media_field(fi)
                    rich = _extract_rich_text_field(fi)
                    cells.append(_render_value(value, media_field=media, rich_text_field=rich))
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


class SortableTable(Component):
    """ModelTable with sortable column headers via htmx.

    Column headers become htmx links that GET ``sort_url`` with
    ``?sort=field&order=asc|desc`` query parameters.

    Args:
        model: Pydantic BaseModel class.
        rows: List of model instances.
        sort_url: Base URL for sort requests.
        table_id: Container id for htmx target (default "sortable-table").
        current_sort: Currently sorted field name.
        current_order: Current sort order ("asc" or "desc").
        csv_url: If set, show an "Export CSV" button linking here.
        exclude: Field names to exclude.
        include: Field names to include.
        zebra: Use zebra striping.
        compact: Use compact size.
        cell_renderers: Dict of field_name → callable(value) for custom rendering.
        extra_columns: Dict of column_name → callable(row) for extra columns.
    """

    tag = "div"

    def __init__(
        self,
        model: type[BaseModel],
        *,
        rows: list[BaseModel],
        sort_url: str,
        table_id: str = "sortable-table",
        current_sort: str | None = None,
        current_order: str = "asc",
        csv_url: str | None = None,
        exclude: set[str] | list[str] | None = None,
        include: set[str] | list[str] | None = None,
        zebra: bool = False,
        compact: bool = False,
        cell_renderers: dict[str, Callable[[Any], Any]] | None = None,
        extra_columns: dict[str, Callable[[BaseModel], Any]] | None = None,
        **attrs: Any,
    ) -> None:
        from kokage_ui.elements import Table as BaseTable

        fields = _filter_fields(model, include, exclude)
        cell_renderers = cell_renderers or {}
        extra_columns = extra_columns or {}

        # Build header cells with sort links
        header_cells = []
        for name, fi in fields:
            label = fi.title or name.replace("_", " ").title()
            if current_sort == name:
                indicator = " \u2191" if current_order == "asc" else " \u2193"
                next_order = "desc" if current_order == "asc" else "asc"
            else:
                indicator = ""
                next_order = "asc"
            link = A(
                f"{label}{indicator}",
                hx_get=f"{sort_url}?sort={name}&order={next_order}",
                hx_target=f"#{table_id}",
                style="cursor:pointer",
            )
            header_cells.append(Th(link))

        for col_name in extra_columns:
            header_cells.append(Th(col_name))

        # Build body rows
        body_rows = []
        for row in rows:
            cells = []
            for name, _fi in fields:
                value = getattr(row, name)
                if name in cell_renderers:
                    cells.append(Td(cell_renderers[name](value)))
                else:
                    cells.append(Td(_render_value(value)))
            for renderer in extra_columns.values():
                cells.append(Td(renderer(row)))
            body_rows.append(Tr(*cells))

        table_cls_parts = ["table"]
        if zebra:
            table_cls_parts.append("table-zebra")
        if compact:
            table_cls_parts.append("table-xs")
        table_cls = " ".join(table_cls_parts)

        table = BaseTable(
            Thead(Tr(*header_cells)),
            Tbody(*body_rows),
            cls=table_cls,
        )

        children: list[Any] = [table]

        if csv_url:
            children.append(
                Div(
                    A("Export CSV", href=csv_url, cls="btn btn-outline btn-sm mt-2"),
                    cls="mt-2",
                )
            )

        attrs["id"] = table_id
        super().__init__(*children, **attrs)


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
            media = _extract_media_field(fi)
            rich = _extract_rich_text_field(fi)
            rendered = _render_value(value, media_field=media, rich_text_field=rich)
            rows.append(
                Div(
                    Strong(label_text, cls="text-sm opacity-70"),
                    Div(rendered, cls="text-lg"),
                    cls="py-2",
                )
            )

        card = Card(*rows, title=card_title)
        super().__init__(card, **attrs)
