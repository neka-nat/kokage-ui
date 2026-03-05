"""DaisyUI high-level components.

Abstracts DaisyUI class structure so you can build UI with Python args alone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dataclasses import dataclass, field

from kokage_ui.elements import (
    A,
    Component,
    Div,
    Figure,
    Form,
    H2,
    H3,
    Img,
    Input,
    Label,
    Li,
    Option,
    Span,
    Tbody,
    Td,
    Th,
    Thead,
    Tr,
    Ul,
)

if TYPE_CHECKING:
    from kokage_ui.page import Page


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


# ========================================
# Toast
# ========================================


class Toast(Component):
    """DaisyUI Toast notification component.

    Args:
        *children: Toast content.
        variant: Alert variant (info, success, warning, error).
        position: DaisyUI toast position classes.
    """

    tag = "div"

    def __init__(
        self,
        *children: Any,
        variant: str = "info",
        position: str = "toast-end toast-top",
        **attrs: Any,
    ) -> None:
        alert = Alert(*children, variant=variant)
        attrs["cls"] = _merge_cls(f"toast {position} z-50", attrs.get("cls"))
        super().__init__(alert, **attrs)


# ========================================
# Layout
# ========================================


class Layout:
    """Reusable page layout configuration.

    NOT a Component subclass — a settings/builder object that wraps content
    in a consistent Page structure with navbar, sidebar, footer, etc.

    Args:
        navbar: NavBar or component for the top of the page.
        sidebar: Component for a left sidebar.
        footer: Component for the page footer.
        theme: DaisyUI theme name.
        title_suffix: Appended to every page title.
        include_toast: Enable toast notification support.
        include_sse: Load htmx SSE extension.
        lang: HTML lang attribute.
    """

    def __init__(
        self,
        *,
        navbar: Any = None,
        sidebar: Any = None,
        footer: Any = None,
        theme: str = "light",
        title_suffix: str = "",
        include_toast: bool = False,
        include_sse: bool = False,
        lang: str = "ja",
    ) -> None:
        self.navbar = navbar
        self.sidebar = sidebar
        self.footer = footer
        self.theme = theme
        self.title_suffix = title_suffix
        self.include_toast = include_toast
        self.include_sse = include_sse
        self.lang = lang

    def wrap(self, content: Any, title: str = "") -> Page:
        """Wrap content in a full Page with the configured layout.

        Compatible with CRUDRouter's page_wrapper(content, title) signature.
        """
        from kokage_ui.page import Page as PageCls

        page_children: list[Any] = []
        if self.navbar is not None:
            page_children.append(self.navbar)

        if self.sidebar is not None:
            main_content = Div(content, cls="flex-1")
            page_children.append(Div(self.sidebar, main_content, cls="flex"))
        else:
            page_children.append(content)

        if self.footer is not None:
            page_children.append(self.footer)

        full_title = f"{title}{self.title_suffix}" if title else self.title_suffix

        return PageCls(
            *page_children,
            title=full_title,
            theme=self.theme,
            include_toast=self.include_toast,
            include_sse=self.include_sse,
            lang=self.lang,
        )


# ========================================
# Modal
# ========================================


class Modal(Component):
    """DaisyUI Modal (dialog) component.

    Args:
        *children: Content inside modal-box.
        modal_id: Required id for JS `.showModal()`.
        title: Optional title rendered as H3.
        actions: Components for modal-action area.
        closable: Add backdrop form to close on outside click.
    """

    tag = "dialog"

    def __init__(
        self,
        *children: Any,
        modal_id: str,
        title: str | None = None,
        actions: list[Any] | None = None,
        closable: bool = True,
        **attrs: Any,
    ) -> None:
        attrs["id"] = modal_id
        attrs["cls"] = _merge_cls("modal", attrs.get("cls"))

        box_children: list[Any] = []
        if title:
            box_children.append(H3(title, cls="font-bold text-lg"))
        box_children.extend(children)
        if actions:
            box_children.append(Div(*actions, cls="modal-action"))

        built: list[Any] = [Div(*box_children, cls="modal-box")]
        if closable:
            built.append(Form(method="dialog", cls="modal-backdrop"))

        super().__init__(*built, **attrs)


# ========================================
# Drawer
# ========================================


class Drawer(Component):
    """DaisyUI Drawer component.

    Args:
        content: Main area content (keyword-only).
        side: Sidebar content (keyword-only).
        drawer_id: Checkbox id for toggling.
        end: Place drawer on the right.
        open: Initially open.
    """

    tag = "div"

    def __init__(
        self,
        *,
        content: Any,
        side: Any,
        drawer_id: str = "kokage-drawer",
        end: bool = False,
        open: bool = False,
        **attrs: Any,
    ) -> None:
        cls_parts = ["drawer"]
        if end:
            cls_parts.append("drawer-end")
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))

        toggle_attrs: dict[str, Any] = {
            "id": drawer_id,
            "type": "checkbox",
            "cls": "drawer-toggle",
        }
        if open:
            toggle_attrs["checked"] = True

        built: list[Any] = [
            Input(**toggle_attrs),
            Div(content, cls="drawer-content"),
            Div(
                Label(side, cls="drawer-overlay", **{"for": drawer_id}),
                cls="drawer-side",
            ),
        ]

        super().__init__(*built, **attrs)


# ========================================
# Tabs
# ========================================


@dataclass
class Tab:
    """Single tab definition for Tabs component."""

    label: str
    content: Any = None
    active: bool = False
    disabled: bool = False
    href: str | None = None


_TAB_VARIANTS = {
    "bordered": "tabs-bordered",
    "lifted": "tabs-lifted",
    "boxed": "tabs-boxed",
}

_TAB_SIZES = {
    "xs": "tabs-xs",
    "sm": "tabs-sm",
    "md": "tabs-md",
    "lg": "tabs-lg",
}


class Tabs(Component):
    """DaisyUI Tabs component.

    Auto-detects mode: if any tab has `content`, uses radio-based
    pure-CSS switching; otherwise uses link/anchor mode (htmx-friendly).

    Args:
        tabs: List of Tab instances.
        variant: bordered, lifted, or boxed.
        size: xs, sm, md, lg.
    """

    tag = "div"

    def __init__(
        self,
        *,
        tabs: list[Tab],
        variant: str | None = None,
        size: str | None = None,
        **attrs: Any,
    ) -> None:
        has_content = any(t.content is not None for t in tabs)

        tabs_cls_parts = ["tabs"]
        if variant and variant in _TAB_VARIANTS:
            tabs_cls_parts.append(_TAB_VARIANTS[variant])
        if size and size in _TAB_SIZES:
            tabs_cls_parts.append(_TAB_SIZES[size])
        tabs_cls = " ".join(tabs_cls_parts)

        if has_content:
            # Radio-based tabs with content panels
            built: list[Any] = []
            attrs["role"] = "tablist"
            attrs["cls"] = _merge_cls(tabs_cls, attrs.get("cls"))
            for i, tab in enumerate(tabs):
                tab_attrs: dict[str, Any] = {
                    "type": "radio",
                    "name": "kokage-tabs",
                    "cls": "tab",
                    "aria_label": tab.label,
                }
                if tab.active:
                    tab_attrs["checked"] = True
                if tab.disabled:
                    tab_attrs["disabled"] = True
                built.append(Input(**tab_attrs))
                panel_content = tab.content if tab.content is not None else ""
                built.append(
                    Div(panel_content, cls="tab-content p-4", role="tabpanel")
                )
            super().__init__(*built, **attrs)
        else:
            # Link-based tabs
            tab_links: list[Any] = []
            for tab in tabs:
                link_cls_parts = ["tab"]
                if tab.active:
                    link_cls_parts.append("tab-active")
                if tab.disabled:
                    link_cls_parts.append("tab-disabled")
                link_cls = " ".join(link_cls_parts)
                if tab.href:
                    tab_links.append(A(tab.label, href=tab.href, cls=link_cls))
                else:
                    tab_links.append(A(tab.label, cls=link_cls))
            attrs["cls"] = _merge_cls(tabs_cls, attrs.get("cls"))
            attrs["role"] = "tablist"
            super().__init__(*tab_links, **attrs)


# ========================================
# Steps
# ========================================

_STEP_COLORS = {
    "primary": "step-primary",
    "secondary": "step-secondary",
    "accent": "step-accent",
    "info": "step-info",
    "success": "step-success",
    "warning": "step-warning",
    "error": "step-error",
    "neutral": "step-neutral",
}


@dataclass
class Step:
    """Single step definition for Steps component."""

    label: str
    data_content: str | None = None
    color: str | None = None


class Steps(Component):
    """DaisyUI Steps component.

    Args:
        steps: List of Step instances.
        current: 0-indexed; steps at index <= current get the color.
        color: Color for completed steps.
        vertical: Vertical layout.
    """

    tag = "ul"

    def __init__(
        self,
        *,
        steps: list[Step],
        current: int = 0,
        color: str = "primary",
        vertical: bool = False,
        **attrs: Any,
    ) -> None:
        cls_parts = ["steps"]
        if vertical:
            cls_parts.append("steps-vertical")
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))

        built: list[Any] = []
        for i, step in enumerate(steps):
            step_cls_parts = ["step"]
            if i <= current:
                step_color = step.color or color
                color_cls = _STEP_COLORS.get(step_color)
                if color_cls:
                    step_cls_parts.append(color_cls)
            li_attrs: dict[str, Any] = {"cls": " ".join(step_cls_parts)}
            if step.data_content is not None:
                li_attrs["data_content"] = step.data_content
            built.append(Li(step.label, **li_attrs))

        super().__init__(*built, **attrs)


# ========================================
# Breadcrumb
# ========================================


class Breadcrumb(Component):
    """DaisyUI Breadcrumb component.

    Args:
        items: List of (label, href) tuples. href=None for current page.
    """

    tag = "div"

    def __init__(
        self,
        *,
        items: list[tuple[str, str | None]],
        **attrs: Any,
    ) -> None:
        attrs["cls"] = _merge_cls("breadcrumbs text-sm", attrs.get("cls"))

        li_children: list[Any] = []
        for label, href in items:
            if href:
                li_children.append(Li(A(label, href=href)))
            else:
                li_children.append(Li(Span(label)))

        super().__init__(Ul(*li_children), **attrs)


# ========================================
# Collapse / Accordion
# ========================================

_COLLAPSE_VARIANTS = {
    "arrow": "collapse-arrow",
    "plus": "collapse-plus",
}


class Collapse(Component):
    """DaisyUI Collapse component.

    Args:
        title: Title text (first positional arg).
        *children: Hidden content.
        open: Initially open.
        variant: arrow or plus.
        name: Group name for radio-based accordion.
    """

    tag = "div"

    def __init__(
        self,
        title: str,
        *children: Any,
        open: bool = False,
        variant: str | None = None,
        name: str | None = None,
        **attrs: Any,
    ) -> None:
        cls_parts = ["collapse", "bg-base-200"]
        if variant and variant in _COLLAPSE_VARIANTS:
            cls_parts.append(_COLLAPSE_VARIANTS[variant])
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))

        if name:
            # Radio-based (for accordion grouping)
            toggle_attrs: dict[str, Any] = {"type": "radio", "name": name}
            if open:
                toggle_attrs["checked"] = True
            built: list[Any] = [
                Input(**toggle_attrs),
                Div(title, cls="collapse-title text-xl font-medium"),
                Div(*children, cls="collapse-content"),
            ]
        else:
            # Checkbox-based (standalone)
            toggle_attrs = {"type": "checkbox"}
            if open:
                toggle_attrs["checked"] = True
            built = [
                Input(**toggle_attrs),
                Div(title, cls="collapse-title text-xl font-medium"),
                Div(*children, cls="collapse-content"),
            ]

        super().__init__(*built, **attrs)


class Accordion(Component):
    """DaisyUI Accordion — multiple Collapse items linked by radio name.

    Args:
        items: List of (title, content) tuples (keyword-only).
        name: Shared radio name for mutual exclusion.
        variant: arrow or plus.
        default_open: Index of the initially open item.
    """

    tag = "div"

    def __init__(
        self,
        *,
        items: list[tuple[str, Any]],
        name: str = "accordion",
        variant: str | None = None,
        default_open: int | None = None,
        **attrs: Any,
    ) -> None:
        built: list[Any] = []
        for i, (title, content) in enumerate(items):
            is_open = default_open == i
            built.append(
                Collapse(
                    title,
                    content,
                    open=is_open,
                    variant=variant,
                    name=name,
                )
            )
        super().__init__(*built, **attrs)


# ========================================
# Dropdown
# ========================================

_DROPDOWN_POSITIONS = {
    "top": "dropdown-top",
    "bottom": "dropdown-bottom",
    "left": "dropdown-left",
    "right": "dropdown-right",
    "end": "dropdown-end",
}


class FileUpload(Component):
    """DaisyUI file-input component with label.

    Args:
        name: Input name attribute.
        label: Label text.
        accept: Accepted file types (e.g., "image/*", ".pdf,.doc").
        multiple: Allow multiple files.
        color: DaisyUI color variant.
        size: DaisyUI size variant (xs, sm, md, lg).
        bordered: Use bordered style.
    """

    tag = "div"

    def __init__(
        self,
        *,
        name: str,
        label: str | None = None,
        accept: str | None = None,
        multiple: bool = False,
        color: str | None = None,
        size: str | None = None,
        bordered: bool = True,
        **attrs: Any,
    ) -> None:
        cls_parts = ["file-input"]
        if bordered:
            cls_parts.append("file-input-bordered")
        if color:
            cls_parts.append(f"file-input-{color}")
        if size:
            cls_parts.append(f"file-input-{size}")
        cls_parts.append("w-full")

        input_attrs: dict[str, Any] = {
            "type": "file",
            "name": name,
            "cls": " ".join(cls_parts),
        }
        if accept:
            input_attrs["accept"] = accept
        if multiple:
            input_attrs["multiple"] = True

        children: list[Any] = []
        if label:
            children.append(Label(Span(label, cls="label-text"), cls="label"))
        children.append(Input(**input_attrs))

        attrs["cls"] = _merge_cls("form-control w-full", attrs.get("cls"))
        super().__init__(*children, **attrs)


class DropZone(Component):
    """Drag-and-drop file upload zone with htmx.

    Renders a dashed-border drop area with a hidden file input.
    Files trigger an htmx upload on change.

    Args:
        name: Input name attribute.
        upload_url: URL to POST files to.
        target: htmx target selector for the response.
        accept: Accepted file types.
        multiple: Allow multiple files.
        text: Instructional text inside the drop zone.
        swap: htmx swap method.
    """

    tag = "div"

    def __init__(
        self,
        *,
        name: str,
        upload_url: str,
        target: str = "",
        accept: str | None = None,
        multiple: bool = False,
        text: str = "Drop files here or click to upload",
        swap: str = "innerHTML",
        **attrs: Any,
    ) -> None:
        input_attrs: dict[str, Any] = {
            "type": "file",
            "name": name,
            "cls": "hidden",
        }
        if accept:
            input_attrs["accept"] = accept
        if multiple:
            input_attrs["multiple"] = True

        file_input = Input(**input_attrs)

        zone_attrs: dict[str, Any] = {
            "cls": _merge_cls(
                "border-2 border-dashed border-base-300 rounded-lg p-8 "
                "text-center cursor-pointer hover:border-primary transition-colors",
                attrs.pop("cls", None),
            ),
            "hx_post": upload_url,
            "hx_encoding": "multipart/form-data",
            "hx_trigger": "change from:find input[type=file]",
            "hx_swap": swap,
            "onclick": "this.querySelector('input[type=file]').click()",
        }
        if target:
            zone_attrs["hx_target"] = target

        super().__init__(
            Span(text, cls="text-base-content/60"),
            file_input,
            **zone_attrs,
        )


class DependentSelect(Component):
    """Select whose options reload when a parent field changes.

    Uses htmx to fetch new options from the server when the parent
    field's value changes.

    Args:
        name: Select name attribute.
        depends_on: Name of the parent field to watch.
        url: URL to fetch options from.
        label: Label text.
        placeholder: Placeholder option text.
        bordered: Use bordered style.
    """

    tag = "div"

    def __init__(
        self,
        *,
        name: str,
        depends_on: str,
        url: str,
        label: str | None = None,
        placeholder: str = "Select...",
        bordered: bool = True,
        **attrs: Any,
    ) -> None:
        from kokage_ui.elements import Select as BaseSelect

        select_cls_parts = ["select", "w-full"]
        if bordered:
            select_cls_parts.append("select-bordered")

        select_el = BaseSelect(
            Option(placeholder, value="", disabled=True, selected=True),
            name=name,
            cls=" ".join(select_cls_parts),
            hx_get=url,
            hx_trigger=f"change from:[name='{depends_on}']",
            hx_include=f"[name='{depends_on}']",
            hx_swap="innerHTML",
        )

        children: list[Any] = []
        if label:
            children.append(Label(Span(label, cls="label-text"), cls="label"))
        children.append(select_el)

        attrs["cls"] = _merge_cls("form-control w-full", attrs.get("cls"))
        super().__init__(*children, **attrs)


class Dropdown(Component):
    """DaisyUI Dropdown component.

    Args:
        trigger: Button text or component. Strings auto-wrapped in a btn div.
        *children: Custom dropdown content (alternative to items).
        items: List of (label, href) tuples for auto-generated menu.
        position: top, bottom, left, right, end.
        hover: Open on hover.
        align_end: Align dropdown to the end.
    """

    tag = "div"

    def __init__(
        self,
        trigger: Any,
        *children: Any,
        items: list[tuple[str, str]] | None = None,
        position: str | None = None,
        hover: bool = False,
        align_end: bool = False,
        **attrs: Any,
    ) -> None:
        cls_parts = ["dropdown"]
        if position and position in _DROPDOWN_POSITIONS:
            cls_parts.append(_DROPDOWN_POSITIONS[position])
        if hover:
            cls_parts.append("dropdown-hover")
        if align_end:
            cls_parts.append("dropdown-end")
        attrs["cls"] = _merge_cls(" ".join(cls_parts), attrs.get("cls"))

        # Build trigger
        if isinstance(trigger, str):
            trigger_el = Div(trigger, tabindex="0", role="button", cls="btn m-1")
        else:
            trigger_el = trigger

        # Build dropdown content
        if children:
            dropdown_content = list(children)
        elif items:
            menu_items = [Li(A(label, href=href)) for label, href in items]
            dropdown_content = [
                Ul(
                    *menu_items,
                    tabindex="0",
                    cls="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow",
                )
            ]
        else:
            dropdown_content = []

        super().__init__(trigger_el, *dropdown_content, **attrs)
