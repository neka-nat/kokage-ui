"""Tests for Markdown component."""

import pytest

from kokage_ui.markdown import Markdown, _sanitize_html


class TestSanitizeHtml:
    def test_strips_script_tags(self):
        html = '<p>Hello</p><script>alert("xss")</script><p>World</p>'
        result = _sanitize_html(html)
        assert "<script" not in result
        assert "alert" not in result
        assert "<p>Hello</p>" in result

    def test_strips_style_tags(self):
        html = "<style>body{display:none}</style><p>Hi</p>"
        result = _sanitize_html(html)
        assert "<style" not in result
        assert "<p>Hi</p>" in result

    def test_strips_iframe_tags(self):
        html = '<iframe src="evil.com"></iframe><p>Safe</p>'
        result = _sanitize_html(html)
        assert "<iframe" not in result
        assert "<p>Safe</p>" in result

    def test_strips_on_attributes(self):
        html = '<div onclick="alert(1)">Click</div>'
        result = _sanitize_html(html)
        assert "onclick" not in result

    def test_preserves_safe_html(self):
        html = "<p>Hello <strong>world</strong></p>"
        result = _sanitize_html(html)
        assert result == html


class TestMarkdown:
    def test_basic_rendering(self):
        m = Markdown("# Hello")
        result = str(m)
        assert "<h1>" in result
        assert "Hello" in result

    def test_bold_text(self):
        m = Markdown("Some **bold** text.")
        result = str(m)
        assert "<strong>bold</strong>" in result

    def test_prose_classes(self):
        m = Markdown("text")
        result = str(m)
        assert "prose" in result
        assert "prose-base" in result
        assert "max-w-none" in result

    def test_custom_prose_size(self):
        m = Markdown("text", prose_size="prose-lg")
        result = str(m)
        assert "prose-lg" in result

    def test_fenced_code_default(self):
        m = Markdown("```python\nprint('hi')\n```")
        result = str(m)
        assert "<code" in result

    def test_tables_extension_default(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        m = Markdown(md)
        result = str(m)
        assert "<table>" in result

    def test_untrusted_strips_script(self):
        m = Markdown('<script>alert("xss")</script>\n\nHello')
        result = str(m)
        assert "<script" not in result
        assert "Hello" in result

    def test_trusted_keeps_script(self):
        m = Markdown('<script>alert("ok")</script>\n\nHello', trusted=True)
        result = str(m)
        assert "<script>" in result

    def test_custom_extensions(self):
        m = Markdown("text", extensions=[])
        result = str(m)
        assert "text" in result

    def test_extra_cls(self):
        m = Markdown("text", cls="my-class")
        result = str(m)
        assert "my-class" in result
        assert "prose" in result
