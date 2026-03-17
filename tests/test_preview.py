"""Tests for FilePreview component and content detection."""

import json

from kokage_ui.ai.preview import (
    FilePreview,
    detect_content_type,
    render_csv_table,
    render_json_tree,
    render_preview,
)


class TestDetectContentType:
    def test_json_hint(self):
        assert detect_content_type("anything", hint="json") == "json"

    def test_csv_hint(self):
        assert detect_content_type("anything", hint="csv") == "csv"

    def test_tsv_hint(self):
        assert detect_content_type("anything", hint="tsv") == "csv"

    def test_markdown_hint(self):
        assert detect_content_type("anything", hint="md") == "markdown"
        assert detect_content_type("anything", hint="markdown") == "markdown"

    def test_image_hint(self):
        assert detect_content_type("anything", hint="image") == "image"

    def test_code_hint(self):
        assert detect_content_type("anything", hint="python") == "code"
        assert detect_content_type("anything", hint="javascript") == "code"

    def test_json_auto_detect_object(self):
        assert detect_content_type('{"key": "value"}') == "json"

    def test_json_auto_detect_array(self):
        assert detect_content_type('[1, 2, 3]') == "json"

    def test_json_auto_detect_with_whitespace(self):
        assert detect_content_type('  {"key": "value"}  ') == "json"

    def test_invalid_json_not_detected(self):
        assert detect_content_type('{not valid json}') == "text"

    def test_csv_auto_detect(self):
        content = "name,age,city\nAlice,30,Tokyo\nBob,25,Osaka"
        assert detect_content_type(content) == "csv"

    def test_csv_tab_separated(self):
        content = "name\tage\tcity\nAlice\t30\tTokyo\nBob\t25\tOsaka"
        assert detect_content_type(content) == "csv"

    def test_csv_needs_multiple_lines(self):
        assert detect_content_type("a,b,c") == "text"

    def test_csv_inconsistent_columns(self):
        content = "a,b,c\nd,e\nf,g,h,i"
        assert detect_content_type(content) == "text"

    def test_image_url_detection(self):
        assert detect_content_type(url="/uploads/photo.png") == "image"
        assert detect_content_type(url="/img/cat.jpg") == "image"
        assert detect_content_type(url="/img/cat.JPEG") == "image"
        assert detect_content_type(url="/img/icon.svg") == "image"
        assert detect_content_type(url="/img/photo.webp") == "image"

    def test_non_image_url(self):
        assert detect_content_type(url="/api/data.json") == "text"

    def test_url_with_query_params(self):
        assert detect_content_type(url="/img/photo.png?w=100") == "image"

    def test_empty_content(self):
        assert detect_content_type("") == "text"

    def test_plain_text(self):
        assert detect_content_type("Hello world") == "text"

    def test_hint_takes_priority(self):
        assert detect_content_type('{"key": "val"}', hint="csv") == "csv"


class TestRenderJsonTree:
    def test_empty_object(self):
        html = render_json_tree({})
        assert "{}" in html

    def test_empty_array(self):
        html = render_json_tree([])
        assert "[]" in html

    def test_string_value(self):
        html = render_json_tree("hello")
        assert "hello" in html
        assert "text-success" in html

    def test_number_value(self):
        html = render_json_tree(42)
        assert "42" in html
        assert "text-secondary" in html

    def test_boolean_value(self):
        html = render_json_tree(True)
        assert "true" in html
        assert "text-warning" in html

    def test_null_value(self):
        html = render_json_tree(None)
        assert "null" in html

    def test_object_with_keys(self):
        html = render_json_tree({"name": "Alice", "age": 30})
        assert "name" in html
        assert "Alice" in html
        assert "30" in html
        assert "text-info" in html

    def test_nested_object(self):
        html = render_json_tree({"user": {"name": "Alice"}})
        assert "details" in html
        assert "Alice" in html

    def test_array_items(self):
        html = render_json_tree([1, 2, 3])
        assert "3 items" not in html  # top-level, no summary
        assert "1" in html
        assert "2" in html
        assert "3" in html

    def test_max_depth(self):
        deep = {"a": {"b": {"c": {"d": "end"}}}}
        html = render_json_tree(deep, max_depth=2)
        assert "..." in html

    def test_xss_escape(self):
        html = render_json_tree({"key": "<script>alert(1)</script>"})
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestRenderCsvTable:
    def test_basic_csv(self):
        content = "name,age\nAlice,30\nBob,25"
        html = render_csv_table(content)
        assert "<table" in html
        assert "table-zebra" in html
        assert "Alice" in html
        assert "Bob" in html
        assert "name" in html
        assert "age" in html

    def test_empty_csv(self):
        html = render_csv_table("")
        assert "<pre" in html

    def test_max_rows(self):
        lines = ["col1,col2"] + [f"a{i},b{i}" for i in range(200)]
        content = "\n".join(lines)
        html = render_csv_table(content, max_rows=10)
        assert "more rows" in html
        assert "190" in html  # 200 - 10

    def test_xss_escape(self):
        content = "name\n<script>alert(1)</script>"
        html = render_csv_table(content)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestRenderPreview:
    def test_json_content(self):
        html = render_preview('{"key": "value"}')
        assert "text-info" in html
        assert "key" in html

    def test_csv_content(self):
        html = render_preview("a,b\n1,2\n3,4")
        assert "<table" in html

    def test_code_with_hint(self):
        html = render_preview("def hello(): pass", hint="python")
        assert "language-python" in html
        assert "<code" in html

    def test_image_url(self):
        html = render_preview(url="/img/photo.png")
        assert "<img" in html
        assert "/img/photo.png" in html

    def test_plain_text_fallback(self):
        html = render_preview("Hello world")
        assert "<pre" in html
        assert "Hello world" in html

    def test_invalid_json_fallback(self):
        html = render_preview("{bad json", hint="json")
        assert "<pre" in html

    def test_markdown_hint(self):
        html = render_preview("# Hello", hint="md")
        assert "prose" in html


class TestFilePreview:
    def test_render_json(self):
        preview = FilePreview('{"name": "Alice"}')
        html = str(preview)
        assert "<div" in html
        assert "Alice" in html
        assert "text-info" in html

    def test_render_csv(self):
        preview = FilePreview("name,age\nAlice,30\nBob,25")
        html = str(preview)
        assert "<table" in html
        assert "Alice" in html

    def test_render_code(self):
        preview = FilePreview("print('hello')", hint="python")
        html = str(preview)
        assert "language-python" in html

    def test_render_image(self):
        preview = FilePreview(url="/img/photo.png")
        html = str(preview)
        assert "<img" in html
        assert "/img/photo.png" in html

    def test_render_plain_text(self):
        preview = FilePreview("Hello world")
        html = str(preview)
        assert "Hello world" in html

    def test_custom_attrs(self):
        preview = FilePreview("test", cls="my-class")
        html = str(preview)
        assert "my-class" in html

    def test_xss_escape(self):
        preview = FilePreview('<script>alert(1)</script>')
        html = str(preview)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_max_depth(self):
        deep = json.dumps({"a": {"b": {"c": "d"}}})
        preview = FilePreview(deep, max_depth=1)
        html = str(preview)
        assert "..." in html


class TestAgentEventPreviewHint:
    def test_preview_hint_field(self):
        from kokage_ui.ai.agent import AgentEvent

        e = AgentEvent(
            type="tool_result",
            call_id="tc1",
            result='[1, 2, 3]',
            preview_hint="json",
        )
        assert e.preview_hint == "json"

    def test_to_dict_includes_preview_hint(self):
        from kokage_ui.ai.agent import AgentEvent

        e = AgentEvent(
            type="tool_result",
            call_id="tc1",
            result="data",
            preview_hint="csv",
        )
        d = e.to_dict()
        assert d["preview_hint"] == "csv"

    def test_to_dict_omits_empty_preview_hint(self):
        from kokage_ui.ai.agent import AgentEvent

        e = AgentEvent(type="tool_result", call_id="tc1", result="data")
        d = e.to_dict()
        assert "preview_hint" not in d


class TestToolCallPreviewHint:
    def test_preview_hint_field(self):
        from kokage_ui.ai.agent import ToolCall

        tc = ToolCall(
            name="search",
            result='{"items": []}',
            preview_hint="json",
        )
        assert tc.preview_hint == "json"

    def test_default_empty(self):
        from kokage_ui.ai.agent import ToolCall

        tc = ToolCall(name="search")
        assert tc.preview_hint == ""


class TestToolCollapsePreview:
    def test_json_result_renders_tree(self):
        from kokage_ui.ai.agent import ToolCall, _render_tool_collapse

        tc = ToolCall(
            name="search",
            input={"q": "test"},
            result='{"items": [1, 2]}',
            call_id="1",
            preview_hint="json",
        )
        html = _render_tool_collapse(tc)
        assert "text-info" in html  # JSON tree styling
        assert "items" in html

    def test_csv_result_renders_table(self):
        from kokage_ui.ai.agent import ToolCall, _render_tool_collapse

        tc = ToolCall(
            name="export",
            result="name,age\nAlice,30\nBob,25",
            call_id="2",
            preview_hint="csv",
        )
        html = _render_tool_collapse(tc)
        assert "<table" in html
        assert "Alice" in html

    def test_plain_result_renders_pre(self):
        from kokage_ui.ai.agent import ToolCall, _render_tool_collapse

        tc = ToolCall(
            name="echo",
            result="Hello world",
            call_id="3",
        )
        html = _render_tool_collapse(tc)
        assert "<pre" in html
        assert "Hello world" in html

    def test_auto_detect_json(self):
        from kokage_ui.ai.agent import ToolCall, _render_tool_collapse

        tc = ToolCall(
            name="api",
            result='{"status": "ok"}',
            call_id="4",
        )
        html = _render_tool_collapse(tc)
        assert "text-info" in html  # JSON tree
        assert "status" in html


class TestAgentViewPreviewJs:
    def test_render_preview_in_script(self):
        from kokage_ui.ai.agent import AgentView

        view = AgentView(send_url="/api/agent", agent_id="test")
        html = str(view)
        assert "renderPreview" in html
        assert "detectType" in html
        assert "renderJsonTree" in html
        assert "renderCsvTable" in html
