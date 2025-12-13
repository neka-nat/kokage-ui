"""Tests for HTML element system."""

from kokage_ui.elements import (
    A,
    Br,
    Button,
    Component,
    Div,
    Form,
    H1,
    Hr,
    Img,
    Input,
    Li,
    Option,
    P,
    Raw,
    Select,
    Span,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Tr,
    Ul,
    _convert_attr_name,
    _render_attrs,
)


class TestAttrConversion:
    def test_cls_to_class(self):
        assert _convert_attr_name("cls") == "class"

    def test_html_for_to_for(self):
        assert _convert_attr_name("html_for") == "for"

    def test_http_equiv(self):
        assert _convert_attr_name("http_equiv") == "http-equiv"

    def test_underscore_to_hyphen(self):
        assert _convert_attr_name("hx_get") == "hx-get"
        assert _convert_attr_name("data_value") == "data-value"
        assert _convert_attr_name("hx_swap_oob") == "hx-swap-oob"

    def test_no_underscore(self):
        assert _convert_attr_name("id") == "id"
        assert _convert_attr_name("name") == "name"


class TestRenderAttrs:
    def test_basic_attrs(self):
        result = _render_attrs({"id": "main", "cls": "container"})
        assert 'id="main"' in result
        assert 'class="container"' in result

    def test_boolean_true(self):
        result = _render_attrs({"disabled": True})
        assert result == " disabled"

    def test_boolean_false_omitted(self):
        result = _render_attrs({"disabled": False})
        assert result == ""

    def test_none_omitted(self):
        result = _render_attrs({"value": None})
        assert result == ""

    def test_htmx_attrs(self):
        result = _render_attrs({"hx_get": "/api", "hx_target": "#result"})
        assert 'hx-get="/api"' in result
        assert 'hx-target="#result"' in result

    def test_dict_to_json(self):
        result = _render_attrs({"hx_vals": {"key": "value"}})
        assert "hx-vals" in result


class TestComponent:
    def test_simple_div(self):
        assert str(Div("Hello")) == "<div>Hello</div>"

    def test_div_with_class(self):
        assert str(Div("Hello", cls="container")) == '<div class="container">Hello</div>'

    def test_nested_components(self):
        result = str(Div(P("text")))
        assert result == "<div><p>text</p></div>"

    def test_multiple_children(self):
        result = str(Div(P("a"), P("b")))
        assert result == "<div><p>a</p><p>b</p></div>"

    def test_htmx_attributes(self):
        result = str(Div("content", hx_get="/api", hx_target="#result"))
        assert 'hx-get="/api"' in result
        assert 'hx-target="#result"' in result

    def test_boolean_attr(self):
        result = str(Button("Submit", disabled=True))
        assert "<button disabled>Submit</button>" == result

    def test_boolean_false_attr(self):
        result = str(Button("Submit", disabled=False))
        assert result == "<button>Submit</button>"

    def test_none_children_skipped(self):
        result = str(Div("a", None, "b"))
        assert result == "<div>ab</div>"

    def test_list_children_flattened(self):
        items = [Li("a"), Li("b")]
        result = str(Ul(items))
        assert result == "<ul><li>a</li><li>b</li></ul>"

    def test_xss_escaping(self):
        result = str(Div('<script>alert("xss")</script>'))
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_component_child_not_escaped(self):
        result = str(Div(Span("safe")))
        assert "<span>safe</span>" in result


class TestVoidElements:
    def test_img(self):
        result = str(Img(src="/photo.jpg", alt="photo"))
        assert result == '<img src="/photo.jpg" alt="photo" />'

    def test_input(self):
        result = str(Input(type="text", name="q"))
        assert result == '<input type="text" name="q" />'

    def test_br(self):
        assert str(Br()) == "<br />"

    def test_hr(self):
        assert str(Hr()) == "<hr />"


class TestRaw:
    def test_raw_not_escaped(self):
        raw = Raw("<b>bold</b>")
        result = str(Div(raw))
        assert "<b>bold</b>" in result

    def test_raw_str(self):
        assert str(Raw("<em>test</em>")) == "<em>test</em>"


class TestHtmlMethod:
    def test_component_html(self):
        d = Div("text")
        assert d.__html__() == "<div>text</div>"

    def test_raw_html(self):
        r = Raw("<b>bold</b>")
        assert r.__html__() == "<b>bold</b>"


class TestRepr:
    def test_simple_repr(self):
        d = Div("hello", cls="test")
        r = repr(d)
        assert "Div" in r
        assert "hello" in r


class TestComplexStructures:
    def test_table(self):
        result = str(
            Table(
                Thead(Tr(Th("Name"), Th("Age"))),
                Tbody(Tr(Td("Alice"), Td("30"))),
            )
        )
        assert "<table>" in result
        assert "<th>Name</th>" in result
        assert "<td>Alice</td>" in result

    def test_form(self):
        result = str(
            Form(
                Input(type="text", name="q"),
                Button("Search"),
                action="/search",
                method="get",
            )
        )
        assert '<form action="/search" method="get">' in result
        assert '<input type="text" name="q" />' in result

    def test_link_with_href(self):
        result = str(A("Click", href="https://example.com"))
        assert 'href="https://example.com"' in result

    def test_select_options(self):
        result = str(
            Select(
                Option("Red", value="red"),
                Option("Blue", value="blue"),
                name="color",
            )
        )
        assert '<select name="color">' in result
        assert '<option value="red">Red</option>' in result
