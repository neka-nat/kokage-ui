"""DaisyUI high-level components.

Abstracts DaisyUI class structure so you can build UI with Python args alone.
"""

from __future__ import annotations

from typing import Any

from kokage_ui.elements import (
    Component,
    Div,
    Figure,
    H2,
    Img,
    Option,
    Span,
    Tbody,
    Td,
    Th,
    Thead,
    Tr,
)


def _merge_cls(base: str, extra: str | None) -> str:
    """Merge base DaisyUI classes with user-provided extra classes."""
    if extra:
        return f"{base} {extra}"
    return base


# ========================================
# Card
# ========================================


class Card(Component):
    """DaisyUI Card component.

    Args:
        *children: Content for card-body.
        title: Card title (card-title).
        image: Image URL (placed in figure).
        image_alt: Image alt text.
        actions: Components for card-actions.
        compact: Use compact card (card-sm).
        side: Horizontal layout (lg:card-side).
    """

    tag = "div"

    def __init__(
        self,
        *children: Any,
        title: str | None = None,
        image: str | None = None,
        image_alt: str = "",
        actions: list[Any] | None = None,
        compact: bool = False,
        side: bool = False,
        **attrs: Any,
    ) -> None:
        cls_parts = ["card", "bg-base-100", "shadow-xl"]
        if compact:
            cls_parts.append("card-sm")
        if side:
            cls_parts.append("lg:card-side")

        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))

        built_children: list[Any] = []

        if image:
            built_children.append(Figure(Img(src=image, alt=image_alt)))

        body_children: list[Any] = []
        if title:
            body_children.append(H2(title, cls="card-title"))
        body_children.extend(children)
        if actions:
            body_children.append(Div(*actions, cls="card-actions justify-end"))

        built_children.append(Div(*body_children, cls="card-body"))

        super().__init__(*built_children, **attrs)


# ========================================
# Stat / Stats
# ========================================


class Stat(Component):
    """DaisyUI Stat component (single stat item).

    Args:
        title: Stat title (stat-title).
        value: Stat value (stat-value).
        desc: Stat description (stat-desc).
        figure: Optional figure element.
    """

    tag = "div"

    def __init__(
        self,
        *,
        title: str,
        value: str,
        desc: str | None = None,
        figure: Any = None,
        **attrs: Any,
    ) -> None:
        attrs["cls"] = _merge_cls("stat", attrs.get("cls"))

        children: list[Any] = []
        if figure:
            children.append(Div(figure, cls="stat-figure"))
        children.append(Div(title, cls="stat-title"))
        children.append(Div(value, cls="stat-value"))
        if desc:
            children.append(Div(desc, cls="stat-desc"))

        super().__init__(*children, **attrs)


class Stats(Component):
    """DaisyUI Stats container (wraps multiple Stat components).

    Args:
        *children: Stat components.
        vertical: Stack vertically.
    """

    tag = "div"

    def __init__(self, *children: Any, vertical: bool = False, **attrs: Any) -> None:
        cls_parts = ["stats", "shadow"]
        if vertical:
            cls_parts.append("stats-vertical")
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))
        super().__init__(*children, **attrs)


# ========================================
# Hero
# ========================================


class Hero(Component):
    """DaisyUI Hero component.

    Args:
        *children: Content for hero-content.
        min_height: Minimum height CSS value.
        overlay: Use hero-overlay.
        image: Background image URL.
    """

    tag = "div"

    def __init__(
        self,
        *children: Any,
        min_height: str | None = None,
        overlay: bool = False,
        image: str | None = None,
        **attrs: Any,
    ) -> None:
        attrs["cls"] = _merge_cls("hero", attrs.get("cls"))

        if min_height:
            style = attrs.get("style", "")
            attrs["style"] = f"min-height: {min_height};{' ' + style if style else ''}"

        if image:
            style = attrs.get("style", "")
            attrs["style"] = f"background-image: url({image});{' ' + style if style else ''}"

        built_children: list[Any] = []
        if overlay:
            built_children.append(Div(cls="hero-overlay bg-opacity-60"))
        built_children.append(Div(*children, cls="hero-content text-center"))

        super().__init__(*built_children, **attrs)


# ========================================
# Alert
# ========================================

_ALERT_VARIANTS = {
    "info": "alert-info",
    "success": "alert-success",
    "warning": "alert-warning",
    "error": "alert-error",
}


class Alert(Component):
    """DaisyUI Alert component.

    Args:
        *children: Alert content.
        variant: One of "info", "success", "warning", "error".
    """

    tag = "div"

    def __init__(self, *children: Any, variant: str = "info", **attrs: Any) -> None:
        cls_parts = ["alert"]
        variant_cls = _ALERT_VARIANTS.get(variant)
        if variant_cls:
            cls_parts.append(variant_cls)
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))
        attrs["role"] = "alert"

        wrapped = [Span(*children)]
        super().__init__(*wrapped, **attrs)


# ========================================
# Badge
# ========================================

_BADGE_COLORS = {
    "primary": "badge-primary",
    "secondary": "badge-secondary",
    "accent": "badge-accent",
    "info": "badge-info",
    "success": "badge-success",
    "warning": "badge-warning",
    "error": "badge-error",
    "ghost": "badge-ghost",
    "neutral": "badge-neutral",
}

_BADGE_SIZES = {
    "xs": "badge-xs",
    "sm": "badge-sm",
    "md": "badge-md",
    "lg": "badge-lg",
}


class Badge(Component):
    """DaisyUI Badge component.

    Args:
        *children: Badge text.
        color: Badge color variant.
        outline: Use outline style.
        size: Badge size (xs, sm, md, lg).
    """

    tag = "span"

    def __init__(
        self,
        *children: Any,
        color: str | None = None,
        outline: bool = False,
        size: str | None = None,
        **attrs: Any,
    ) -> None:
        cls_parts = ["badge"]
        if color and color in _BADGE_COLORS:
            cls_parts.append(_BADGE_COLORS[color])
        if outline:
            cls_parts.append("badge-outline")
        if size and size in _BADGE_SIZES:
            cls_parts.append(_BADGE_SIZES[size])
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))
        super().__init__(*children, **attrs)


# ========================================
# NavBar
# ========================================


class NavBar(Component):
    """DaisyUI Navbar component.

    Args:
        start: Content for navbar-start.
        center: Content for navbar-center.
        end: Content for navbar-end.
    """

    tag = "div"

    def __init__(
        self,
        *,
        start: Any = None,
        center: Any = None,
        end: Any = None,
        **attrs: Any,
    ) -> None:
        attrs["cls"] = _merge_cls("navbar bg-base-100 shadow-sm", attrs.get("cls"))

        children: list[Any] = []
        if start:
            children.append(Div(start, cls="navbar-start"))
        if center:
            children.append(Div(center, cls="navbar-center"))
        if end:
            children.append(Div(end, cls="navbar-end"))

        super().__init__(*children, **attrs)


# ========================================
# DaisyButton
# ========================================

_BUTTON_COLORS = {
    "primary": "btn-primary",
    "secondary": "btn-secondary",
    "accent": "btn-accent",
    "info": "btn-info",
    "success": "btn-success",
    "warning": "btn-warning",
    "error": "btn-error",
    "neutral": "btn-neutral",
    "ghost": "btn-ghost",
    "link": "btn-link",
}

_BUTTON_VARIANTS = {
    "outline": "btn-outline",
    "ghost": "btn-ghost",
    "soft": "btn-soft",
    "link": "btn-link",
}

_BUTTON_SIZES = {
    "xs": "btn-xs",
    "sm": "btn-sm",
    "md": "btn-md",
    "lg": "btn-lg",
}


class DaisyButton(Component):
    """DaisyUI styled Button.

    Args:
        *children: Button text.
        color: Button color (primary, secondary, accent, etc.).
        variant: Style variant (outline, ghost, soft, link).
        size: Button size (xs, sm, md, lg).
        loading: Show loading spinner.
        disabled: Disable the button.
    """

    tag = "button"

    def __init__(
        self,
        *children: Any,
        color: str | None = None,
        variant: str | None = None,
        size: str | None = None,
        loading: bool = False,
        disabled: bool = False,
        **attrs: Any,
    ) -> None:
        cls_parts = ["btn"]
        if color and color in _BUTTON_COLORS:
            cls_parts.append(_BUTTON_COLORS[color])
        if variant and variant in _BUTTON_VARIANTS:
            cls_parts.append(_BUTTON_VARIANTS[variant])
        if size and size in _BUTTON_SIZES:
            cls_parts.append(_BUTTON_SIZES[size])
        if loading:
            cls_parts.append("loading")
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))
        if disabled:
            attrs["disabled"] = True
        super().__init__(*children, **attrs)


# ========================================
# Form components
# ========================================


class DaisyInput(Component):
    """DaisyUI styled Input with optional label.

    Args:
        label: Label text.
        type: Input type (default: "text").
        name: Input name attribute.
        placeholder: Placeholder text.
        bordered: Use bordered style.
        required: Mark as required.
    """

    tag = "div"

    def __init__(
        self,
        *,
        label: str | None = None,
        type: str = "text",
        name: str = "",
        placeholder: str = "",
        bordered: bool = True,
        required: bool = False,
        **attrs: Any,
    ) -> None:
        from kokage_ui.elements import Input as BaseInput, Label

        input_cls = "input w-full"
        if bordered:
            input_cls += " input-bordered"

        input_attrs: dict[str, Any] = {
            "type": type,
            "name": name,
            "placeholder": placeholder,
            "cls": input_cls,
        }
        if required:
            input_attrs["required"] = True

        children: list[Any] = []
        if label:
            children.append(Label(Span(label, cls="label-text"), cls="label"))
        children.append(BaseInput(**input_attrs))

        attrs["cls"] = _merge_cls("form-control w-full", attrs.get("cls"))
        super().__init__(*children, **attrs)


class DaisySelect(Component):
    """DaisyUI styled Select with optional label.

    Args:
        options: List of (value, label) tuples or strings.
        label: Label text.
        name: Select name attribute.
        bordered: Use bordered style.
    """

    tag = "div"

    def __init__(
        self,
        *,
        options: list[tuple[str, str] | str],
        label: str | None = None,
        name: str = "",
        bordered: bool = True,
        **attrs: Any,
    ) -> None:
        from kokage_ui.elements import Select as BaseSelect, Label

        select_cls = "select w-full"
        if bordered:
            select_cls += " select-bordered"

        option_elements: list[Any] = []
        for opt in options:
            if isinstance(opt, tuple):
                option_elements.append(Option(opt[1], value=opt[0]))
            else:
                option_elements.append(Option(opt, value=opt))

        children: list[Any] = []
        if label:
            children.append(Label(Span(label, cls="label-text"), cls="label"))
        children.append(BaseSelect(*option_elements, name=name, cls=select_cls))

        attrs["cls"] = _merge_cls("form-control w-full", attrs.get("cls"))
        super().__init__(*children, **attrs)


class DaisyTextarea(Component):
    """DaisyUI styled Textarea with optional label.

    Args:
        label: Label text.
        name: Textarea name attribute.
        placeholder: Placeholder text.
        bordered: Use bordered style.
        rows: Number of rows.
    """

    tag = "div"

    def __init__(
        self,
        *,
        label: str | None = None,
        name: str = "",
        placeholder: str = "",
        bordered: bool = True,
        rows: int = 3,
        **attrs: Any,
    ) -> None:
        from kokage_ui.elements import Textarea as BaseTextarea, Label

        textarea_cls = "textarea w-full"
        if bordered:
            textarea_cls += " textarea-bordered"

        children: list[Any] = []
        if label:
            children.append(Label(Span(label, cls="label-text"), cls="label"))
        children.append(
            BaseTextarea(
                name=name,
                placeholder=placeholder,
                rows=str(rows),
                cls=textarea_cls,
            )
        )

        attrs["cls"] = _merge_cls("form-control w-full", attrs.get("cls"))
        super().__init__(*children, **attrs)


# ========================================
# DaisyTable
# ========================================


class DaisyTable(Component):
    """DaisyUI styled Table.

    Args:
        headers: List of header strings.
        rows: List of rows, each row is a list of cell content.
        zebra: Use zebra striping.
        compact: Use compact (xs) size.
    """

    tag = "div"

    def __init__(
        self,
        *,
        headers: list[str],
        rows: list[list[Any]],
        zebra: bool = False,
        compact: bool = False,
        **attrs: Any,
    ) -> None:
        from kokage_ui.elements import Table as BaseTable

        table_cls_parts = ["table"]
        if zebra:
            table_cls_parts.append("table-zebra")
        if compact:
            table_cls_parts.append("table-xs")
        table_cls = " ".join(table_cls_parts)

        header_row = Tr(*[Th(h) for h in headers])
        body_rows = [Tr(*[Td(cell) for cell in row]) for row in rows]

        table = BaseTable(
            Thead(header_row),
            Tbody(*body_rows),
            cls=table_cls,
        )

        attrs["cls"] = _merge_cls("overflow-x-auto", attrs.get("cls"))
        super().__init__(table, **attrs)
