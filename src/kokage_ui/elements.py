"""HTML element system for kokage.

Class-based HTML generation engine inspired by FastHTML's FT system.
Children are positional args, attributes are keyword args.
"""

from __future__ import annotations

import json
from typing import Any

from markupsafe import Markup, escape

# Attribute name mapping for Python reserved words
_SPECIAL_ATTRS: dict[str, str] = {
    "cls": "class",
    "html_for": "for",
    "http_equiv": "http-equiv",
}

# Void elements (no closing tag)
VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


def _convert_attr_name(name: str) -> str:
    """Convert Python attribute name to HTML attribute name.

    - 'cls' -> 'class'
    - 'html_for' -> 'for'
    - 'http_equiv' -> 'http-equiv'
    - Others: underscore -> hyphen (hx_get -> hx-get)
    """
    if name in _SPECIAL_ATTRS:
        return _SPECIAL_ATTRS[name]
    return name.replace("_", "-")


def _render_attr_value(value: Any) -> str | None:
    """Render an attribute value to an HTML string.

    - True -> None (boolean attribute, name only)
    - False/None -> should be skipped by caller
    - dict -> JSON string
    - Other -> escaped string
    """
    if value is True:
        return None  # boolean attribute
    if isinstance(value, dict):
        return escape(json.dumps(value, ensure_ascii=False))
    return escape(str(value))


def _render_attrs(attrs: dict[str, Any]) -> str:
    """Render attribute dict to HTML attribute string."""
    parts: list[str] = []
    for key, value in attrs.items():
        if value is False or value is None:
            continue
        html_name = _convert_attr_name(key)
        rendered = _render_attr_value(value)
        if rendered is None:  # boolean attribute
            parts.append(f" {html_name}")
        else:
            parts.append(f' {html_name}="{rendered}"')
    return "".join(parts)


def _render_child(child: Any) -> str:
    """Render a single child to HTML string."""
    if child is None:
        return ""
    if isinstance(child, Component):
        return child.render()
    if hasattr(child, "__html__"):
        return child.__html__()
    if isinstance(child, (list, tuple)):
        return "".join(_render_child(item) for item in child)
    return str(escape(str(child)))


class Component:
    """Base class for all HTML elements.

    Children are positional args, attributes are keyword args.

    Example:
        >>> str(Div("Hello", cls="container"))
        '<div class="container">Hello</div>'
        >>> str(Div(P("text"), id="main", hx_get="/api"))
        '<div id="main" hx-get="/api"><p>text</p></div>'
    """

    tag: str = "div"

    def __init__(self, *children: Any, **attrs: Any) -> None:
        self.children: tuple[Any, ...] = children
        self.attrs: dict[str, Any] = attrs

    def render(self) -> str:
        """Generate HTML string."""
        tag = self.tag
        attr_str = _render_attrs(self.attrs)

        if tag in VOID_ELEMENTS:
            return Markup(f"<{tag}{attr_str} />")

        children_html = "".join(_render_child(c) for c in self.children)
        return Markup(f"<{tag}{attr_str}>{children_html}</{tag}>")

    def __str__(self) -> str:
        return self.render()

    def __html__(self) -> str:
        """markupsafe compatible. Called by Jinja2 templates etc."""
        return self.render()

    def __repr__(self) -> str:
        children_repr = ", ".join(repr(c) for c in self.children)
        attrs_repr = ", ".join(f"{k}={v!r}" for k, v in self.attrs.items())
        parts = [p for p in (children_repr, attrs_repr) if p]
        return f"{self.__class__.__name__}({', '.join(parts)})"


class Raw:
    """Insert raw HTML without escaping.

    Only use with trusted HTML content.
    """

    def __init__(self, html: str) -> None:
        self._html = html

    def __html__(self) -> str:
        return self._html

    def __str__(self) -> str:
        return self._html


# ========================================
# Concrete HTML element classes
# ========================================

# --- Sections / Containers ---
class Div(Component):
    tag = "div"


class Span(Component):
    tag = "span"


class Section(Component):
    tag = "section"


class Article(Component):
    tag = "article"


class Aside(Component):
    tag = "aside"


class Header(Component):
    tag = "header"


class Footer(Component):
    tag = "footer"


class Main(Component):
    tag = "main"


class Nav(Component):
    tag = "nav"


# --- Text ---
class P(Component):
    tag = "p"


class H1(Component):
    tag = "h1"


class H2(Component):
    tag = "h2"


class H3(Component):
    tag = "h3"


class H4(Component):
    tag = "h4"


class H5(Component):
    tag = "h5"


class H6(Component):
    tag = "h6"


class Strong(Component):
    tag = "strong"


class Em(Component):
    tag = "em"


class Small(Component):
    tag = "small"


class Pre(Component):
    tag = "pre"


class Code(Component):
    tag = "code"


class Blockquote(Component):
    tag = "blockquote"


# --- Links / Media ---
class A(Component):
    tag = "a"


class Img(Component):
    tag = "img"


class Br(Component):
    tag = "br"


class Hr(Component):
    tag = "hr"


# --- Lists ---
class Ul(Component):
    tag = "ul"


class Ol(Component):
    tag = "ol"


class Li(Component):
    tag = "li"


# --- Table ---
class Table(Component):
    tag = "table"


class Thead(Component):
    tag = "thead"


class Tbody(Component):
    tag = "tbody"


class Tfoot(Component):
    tag = "tfoot"


class Tr(Component):
    tag = "tr"


class Th(Component):
    tag = "th"


class Td(Component):
    tag = "td"


# --- Form ---
class Form(Component):
    tag = "form"


class Button(Component):
    tag = "button"


class Input(Component):
    tag = "input"


class Textarea(Component):
    tag = "textarea"


class Select(Component):
    tag = "select"


class Option(Component):
    tag = "option"


class Label(Component):
    tag = "label"


class Fieldset(Component):
    tag = "fieldset"


class Legend(Component):
    tag = "legend"


# --- Meta / Document ---
class Script(Component):
    tag = "script"


class Style(Component):
    tag = "style"


class Link(Component):
    tag = "link"


class Meta(Component):
    tag = "meta"


class Title(Component):
    tag = "title"


class Head(Component):
    tag = "head"


class Body(Component):
    tag = "body"


class Html(Component):
    tag = "html"


# --- Others ---
class Figure(Component):
    tag = "figure"


class Figcaption(Component):
    tag = "figcaption"


class Details(Component):
    tag = "details"


class Summary(Component):
    tag = "summary"


class Dialog(Component):
    tag = "dialog"


class Progress(Component):
    tag = "progress"


# --- Media ---
class Video(Component):
    tag = "video"


class Audio(Component):
    tag = "audio"


class Picture(Component):
    tag = "picture"


class Canvas(Component):
    tag = "canvas"


class Source(Component):
    tag = "source"


class Track(Component):
    tag = "track"
