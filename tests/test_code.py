"""Tests for CodeBlock component."""

from kokage_ui.features.code import CodeBlock


class TestCodeBlock:
    def test_renders_pre_code(self):
        cb = CodeBlock("print('hi')")
        result = str(cb)
        assert "<pre>" in result
        assert "<code>" in result
        assert "</code></pre>" in result

    def test_escapes_code(self):
        cb = CodeBlock("<script>alert('xss')</script>")
        result = str(cb)
        assert "&lt;script&gt;" in result
        assert "<script>alert" not in result

    def test_language_class(self):
        cb = CodeBlock("x = 1", language="python")
        result = str(cb)
        assert 'class="language-python"' in result

    def test_no_language(self):
        cb = CodeBlock("hello")
        result = str(cb)
        assert "language-" not in result

    def test_copy_button(self):
        cb = CodeBlock("code", copy_button=True)
        result = str(cb)
        assert "Copy</button>" in result
        assert "navigator.clipboard" in result

    def test_no_copy_button_default(self):
        cb = CodeBlock("code")
        result = str(cb)
        assert "Copy</button>" not in result

    def test_hljs_script(self):
        cb = CodeBlock("code")
        result = str(cb)
        assert "hljs.highlightElement" in result
        assert "typeof hljs" in result

    def test_relative_class(self):
        cb = CodeBlock("code")
        result = str(cb)
        assert 'class="relative"' in result

    def test_extra_cls(self):
        cb = CodeBlock("code", cls="my-extra")
        result = str(cb)
        assert "relative" in result
        assert "my-extra" in result

    def test_auto_id(self):
        cb = CodeBlock("code")
        result = str(cb)
        assert "kokage-code-" in result

    def test_iife_wrapper(self):
        cb = CodeBlock("code")
        result = str(cb)
        assert "(function(){" in result
        assert "})()" in result
