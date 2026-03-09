"""Tests for rich text editor support."""

from __future__ import annotations

from typing import Annotated

import pytest
import dataclasses

from pydantic import BaseModel

from kokage_ui.models import (
    ModelDetail,
    ModelForm,
    ModelTable,
    _extract_rich_text_field,
    _field_to_component,
    _render_value,
)
from kokage_ui.page import Page, QUILL_CSS_CDN, QUILL_JS_CDN
from kokage_ui.fields.richtext import RichTextEditor, RichTextField, _TOOLBAR_PRESETS


# --- TestRichTextField ---

class TestRichTextField:
    def test_defaults(self):
        f = RichTextField()
        assert f.height == "300px"
        assert f.toolbar == "standard"
        assert f.placeholder == ""

    def test_custom_values(self):
        f = RichTextField(height="200px", toolbar="minimal", placeholder="Write here")
        assert f.height == "200px"
        assert f.toolbar == "minimal"
        assert f.placeholder == "Write here"

    def test_frozen(self):
        f = RichTextField()
        with pytest.raises(dataclasses.FrozenInstanceError):
            f.height = "100px"  # type: ignore[misc]

    def test_toolbar_presets_exist(self):
        assert "minimal" in _TOOLBAR_PRESETS
        assert "standard" in _TOOLBAR_PRESETS
        assert "full" in _TOOLBAR_PRESETS


# --- TestRichTextEditor ---

class TestRichTextEditor:
    def test_render_contains_editor_div(self):
        editor = RichTextEditor(name="body", editor_id="test-editor")
        html = editor.render()
        assert 'id="test-editor"' in html
        assert 'style="height:300px"' in html

    def test_render_contains_hidden_input(self):
        editor = RichTextEditor(name="body", editor_id="test-editor")
        html = editor.render()
        assert 'type="hidden"' in html
        assert 'name="body"' in html
        assert 'id="test-editor-input"' in html

    def test_render_contains_script(self):
        editor = RichTextEditor(name="body", editor_id="test-editor")
        html = editor.render()
        assert "<script>" in html
        assert "new Quill" in html

    def test_initial_value(self):
        editor = RichTextEditor(name="body", value="<p>Hello</p>", editor_id="test-editor")
        html = editor.render()
        assert "&lt;p&gt;Hello&lt;/p&gt;" in html

    def test_custom_height(self):
        editor = RichTextEditor(name="body", height="500px", editor_id="test-editor")
        html = editor.render()
        assert "height:500px" in html

    def test_custom_placeholder(self):
        editor = RichTextEditor(name="body", placeholder="Write something...", editor_id="test-editor")
        html = editor.render()
        assert "Write something..." in html

    def test_auto_generated_id(self):
        editor = RichTextEditor(name="body")
        html = editor.render()
        assert "kokage-rte-" in html

    def test_xss_escape_value(self):
        editor = RichTextEditor(name="body", value='<script>alert("xss")</script>', editor_id="test-editor")
        html = editor.render()
        assert '<script>alert("xss")</script>' not in html
        assert "&lt;script&gt;" in html

    def test_toolbar_minimal(self):
        editor = RichTextEditor(name="body", toolbar="minimal", editor_id="test-editor")
        html = editor.render()
        assert '"bold"' in html
        assert '"italic"' in html

    def test_htmx_sync(self):
        editor = RichTextEditor(name="body", editor_id="test-editor")
        html = editor.render()
        assert "htmx:configRequest" in html


# --- TestExtractRichTextField ---

class TestExtractRichTextField:
    def test_extract_from_annotated(self):
        class M(BaseModel):
            body: Annotated[str, RichTextField()] = ""

        fi = M.model_fields["body"]
        result = _extract_rich_text_field(fi)
        assert result is not None
        assert isinstance(result, RichTextField)

    def test_extract_returns_none_for_plain_field(self):
        class M(BaseModel):
            name: str = ""

        fi = M.model_fields["name"]
        result = _extract_rich_text_field(fi)
        assert result is None

    def test_extract_custom_params(self):
        class M(BaseModel):
            body: Annotated[str, RichTextField(height="200px", toolbar="full")] = ""

        fi = M.model_fields["body"]
        result = _extract_rich_text_field(fi)
        assert result is not None
        assert result.height == "200px"
        assert result.toolbar == "full"


# --- TestFieldToComponentRichText ---

class TestFieldToComponentRichText:
    def test_richtext_field_generates_editor(self):
        class M(BaseModel):
            body: Annotated[str, RichTextField()] = ""

        fi = M.model_fields["body"]
        comp = _field_to_component("body", fi)
        html = comp.render()
        assert "new Quill" in html
        assert 'name="body"' in html

    def test_richtext_field_with_value(self):
        class M(BaseModel):
            body: Annotated[str, RichTextField()] = ""

        fi = M.model_fields["body"]
        comp = _field_to_component("body", fi, value="<p>Existing</p>")
        html = comp.render()
        assert "&lt;p&gt;Existing&lt;/p&gt;" in html


# --- TestRenderValueRichText ---

class TestRenderValueRichText:
    def test_rich_text_html_preview(self):
        rich = RichTextField()
        result = _render_value("<p>Hello <strong>world</strong></p>", rich_text_field=rich)
        html = result.render()
        assert "prose" in html
        assert "<p>Hello" in html

    def test_rich_text_empty_value(self):
        rich = RichTextField()
        result = _render_value("", rich_text_field=rich)
        # Empty string is falsy, should return str
        assert result == ""

    def test_rich_text_none_value(self):
        rich = RichTextField()
        result = _render_value(None, rich_text_field=rich)
        assert result == "-"


# --- TestPageIncludeQuill ---

class TestPageIncludeQuill:
    def test_include_quill_adds_cdn(self):
        page = Page(title="Test", include_quill=True)
        html = page.render()
        assert QUILL_CSS_CDN in html
        assert QUILL_JS_CDN in html

    def test_default_no_quill(self):
        page = Page(title="Test")
        html = page.render()
        assert "quill" not in html.lower()


# --- TestModelFormRichText ---

class TestModelFormRichText:
    def test_model_form_with_richtext(self):
        class Article(BaseModel):
            title: str = ""
            body: Annotated[str, RichTextField()] = ""

        form = ModelForm(Article, action="/create")
        html = form.render()
        assert "new Quill" in html
        assert 'name="body"' in html

    def test_model_form_edit_mode(self):
        class Article(BaseModel):
            title: str = ""
            body: Annotated[str, RichTextField()] = ""

        instance = Article(title="Test", body="<p>Content</p>")
        form = ModelForm(Article, action="/edit", instance=instance)
        html = form.render()
        assert "&lt;p&gt;Content&lt;/p&gt;" in html


# --- TestModelTableRichText ---

class TestModelTableRichText:
    def test_table_renders_rich_text_preview(self):
        class Article(BaseModel):
            title: str = ""
            body: Annotated[str, RichTextField()] = ""

        rows = [Article(title="Test", body="<p>Hello world</p>")]
        table = ModelTable(Article, rows=rows)
        html = table.render()
        assert "prose" in html


# --- TestModelDetailRichText ---

class TestModelDetailRichText:
    def test_detail_renders_rich_text(self):
        class Article(BaseModel):
            title: str = ""
            body: Annotated[str, RichTextField()] = ""

        instance = Article(title="Test", body="<p>Detail content</p>")
        detail = ModelDetail(instance)
        html = detail.render()
        assert "prose" in html
        assert "<p>Detail content</p>" in html
