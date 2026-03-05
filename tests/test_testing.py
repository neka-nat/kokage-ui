"""Tests for kokage_ui.testing helpers."""

import pytest

from kokage_ui import Card, Div, Page, Raw
from kokage_ui.testing import (
    HTMLAssertions,
    ResponseAssertions,
    assert_response,
    make_app,
    make_client,
    render,
    rendered,
)


# ---- TestRender ----


class TestRender:
    def test_component(self):
        html = render(Div("hello", cls="box"))
        assert "<div" in html
        assert "hello" in html
        assert "box" in html

    def test_page(self):
        html = render(Page(Div("content"), title="Test"))
        assert "<!DOCTYPE html>" in html
        assert "content" in html

    def test_raw(self):
        html = render(Raw("<b>bold</b>"))
        assert "<b>bold</b>" in html

    def test_str_passthrough(self):
        assert render("plain text") == "plain text"

    def test_object_with_render_method(self):
        class Fake:
            def render(self):
                return "<fake/>"

        assert render(Fake()) == "<fake/>"


# ---- TestHTMLAssertions ----


class TestHTMLAssertions:
    def test_has_single(self):
        doc = HTMLAssertions("<div>hello</div>")
        doc.has("hello")

    def test_has_multiple(self):
        doc = HTMLAssertions("<div class='a'>hello</div>")
        doc.has("hello", "class", "div")

    def test_has_fails(self):
        doc = HTMLAssertions("<div>hello</div>")
        with pytest.raises(AssertionError, match="Expected to find"):
            doc.has("missing")

    def test_has_not_success(self):
        doc = HTMLAssertions("<div>hello</div>")
        doc.has_not("missing", "absent")

    def test_has_not_fails(self):
        doc = HTMLAssertions("<div>hello</div>")
        with pytest.raises(AssertionError, match="to NOT be in"):
            doc.has_not("hello")

    def test_has_count(self):
        doc = HTMLAssertions("<li>a</li><li>b</li><li>c</li>")
        doc.has_count("<li>", 3)

    def test_has_count_fails(self):
        doc = HTMLAssertions("<li>a</li><li>b</li>")
        with pytest.raises(AssertionError, match="to appear 3 times, found 2"):
            doc.has_count("<li>", 3)

    def test_has_element_single_attr(self):
        doc = HTMLAssertions('<input type="text" name="foo">')
        doc.has_element("input", type="text")

    def test_has_element_multiple_attrs(self):
        doc = HTMLAssertions('<input type="file" accept="image/*" class="file-input">')
        doc.has_element("input", type="file", accept="image/*")

    def test_has_element_fails(self):
        doc = HTMLAssertions('<input type="text">')
        with pytest.raises(AssertionError, match="No <input"):
            doc.has_element("input", type="file")

    def test_has_no_element_success(self):
        doc = HTMLAssertions('<input type="text">')
        doc.has_no_element("input", type="file")

    def test_has_no_element_fails(self):
        doc = HTMLAssertions('<input type="text">')
        with pytest.raises(AssertionError, match="Found unexpected"):
            doc.has_no_element("input", type="text")

    def test_has_tag(self):
        doc = HTMLAssertions("<table><tr><td>x</td></tr></table>")
        doc.has_tag("table")
        doc.has_tag("tr")
        doc.has_tag("td")

    def test_has_tag_fails(self):
        doc = HTMLAssertions("<div>hello</div>")
        with pytest.raises(AssertionError, match="No <span>"):
            doc.has_tag("span")

    def test_has_no_tag(self):
        doc = HTMLAssertions("<div>hello</div>")
        doc.has_no_tag("span")

    def test_has_no_tag_fails(self):
        doc = HTMLAssertions("<div>hello</div>")
        with pytest.raises(AssertionError, match="Unexpected <div>"):
            doc.has_no_tag("div")

    def test_method_chaining(self):
        doc = HTMLAssertions('<div id="main"><span>hello</span></div>')
        result = (
            doc.has("hello")
            .has_not("missing")
            .has_element("div", id="main")
            .has_tag("span")
            .has_no_tag("table")
        )
        assert result is doc


# ---- TestRendered ----


class TestRendered:
    def test_component_to_assertions(self):
        doc = rendered(Div("hello", cls="box"))
        assert isinstance(doc, HTMLAssertions)
        doc.has("hello", "box")

    def test_card(self):
        rendered(Card("Hello", title="My Card")).has("card-body", "My Card")

    def test_chaining(self):
        rendered(Div("a", cls="b")).has("a").has_not("missing").has_tag("div")


# ---- TestResponseAssertions ----


class TestResponseAssertions:
    def _fake_response(self, status_code=200, text="<div>ok</div>"):
        class FakeResponse:
            pass

        r = FakeResponse()
        r.status_code = status_code
        r.text = text
        return r

    def test_is_ok(self):
        ra = ResponseAssertions(self._fake_response())
        ra.is_ok()

    def test_is_ok_fails(self):
        ra = ResponseAssertions(self._fake_response(status_code=404))
        with pytest.raises(AssertionError, match="Expected 200, got 404"):
            ra.is_ok()

    def test_is_status(self):
        ra = ResponseAssertions(self._fake_response(status_code=201))
        ra.is_status(201)

    def test_is_status_fails(self):
        ra = ResponseAssertions(self._fake_response(status_code=500))
        with pytest.raises(AssertionError, match="Expected 200, got 500"):
            ra.is_status(200)

    def test_has(self):
        ra = ResponseAssertions(self._fake_response(text="<div>hello world</div>"))
        ra.has("hello", "world")

    def test_has_fails(self):
        ra = ResponseAssertions(self._fake_response(text="<div>hello</div>"))
        with pytest.raises(AssertionError, match="Expected.*in response body"):
            ra.has("missing")

    def test_has_not(self):
        ra = ResponseAssertions(self._fake_response(text="<div>hello</div>"))
        ra.has_not("missing")

    def test_has_not_fails(self):
        ra = ResponseAssertions(self._fake_response(text="<div>hello</div>"))
        with pytest.raises(AssertionError, match="Unexpected.*in response body"):
            ra.has_not("hello")

    def test_html_conversion(self):
        ra = ResponseAssertions(self._fake_response(text='<input type="text">'))
        html_doc = ra.html()
        assert isinstance(html_doc, HTMLAssertions)
        html_doc.has_element("input", type="text")

    def test_chaining(self):
        ra = ResponseAssertions(self._fake_response(text="<div>hello</div>"))
        result = ra.is_ok().has("hello").has_not("missing")
        assert isinstance(result, ResponseAssertions)


class TestAssertResponse:
    def test_wraps_response(self):
        class FakeResponse:
            status_code = 200
            text = "<div>ok</div>"

        ra = assert_response(FakeResponse())
        assert isinstance(ra, ResponseAssertions)
        ra.is_ok().has("ok")


# ---- TestMakeApp ----


class TestMakeApp:
    def test_returns_tuple(self):
        from fastapi import FastAPI

        from kokage_ui.core import KokageUI

        app, ui = make_app()
        assert isinstance(app, FastAPI)
        assert isinstance(ui, KokageUI)

    def test_make_client(self):
        app, ui = make_app()

        @ui.page("/test")
        def test_page():
            return Page(Div("hello"), title="Test")

        client = make_client(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "hello" in resp.text


# ---- TestConftest (fixtures from conftest.py) ----


class TestConftest:
    def test_simple_items(self, simple_items):
        assert len(simple_items) == 3
        assert simple_items[0].name == "Alpha"
        assert simple_items[1].name == "Beta"
        assert simple_items[2].name == "Gamma"

    def test_crud_client_get(self, crud_client):
        resp = crud_client.get("/items")
        assert resp.status_code == 200
        assert "Alpha" in resp.text
