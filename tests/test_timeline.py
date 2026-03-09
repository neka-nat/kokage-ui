"""Tests for Timeline component."""

from markupsafe import Markup

from kokage_ui.components import Timeline, TimelineItem
from kokage_ui.elements import Span


class TestTimelineItem:
    def test_defaults(self):
        item = TimelineItem(content="Hello")
        assert item.content == "Hello"
        assert item.label is None
        assert item.color is None
        assert item.icon is None

    def test_all_fields(self):
        item = TimelineItem(content="Content", label="2024", color="primary", icon="★")
        assert item.content == "Content"
        assert item.label == "2024"
        assert item.color == "primary"
        assert item.icon == "★"


class TestTimeline:
    def test_basic_render(self):
        result = str(Timeline(items=[TimelineItem(content="A")]))
        assert "<ul" in result
        assert "timeline" in result

    def test_vertical_default(self):
        result = str(Timeline(items=[TimelineItem(content="A")]))
        assert "timeline-vertical" in result

    def test_horizontal(self):
        result = str(Timeline(items=[TimelineItem(content="A")], vertical=False))
        assert "timeline-horizontal" in result
        assert "timeline-vertical" not in result

    def test_compact(self):
        result = str(Timeline(items=[TimelineItem(content="A")], compact=True))
        assert "timeline-compact" in result

    def test_use_box_default(self):
        result = str(Timeline(items=[TimelineItem(content="A")]))
        assert "timeline-box" in result

    def test_use_box_false(self):
        result = str(Timeline(items=[TimelineItem(content="A")], use_box=False))
        assert "timeline-box" not in result
        assert "timeline-end" in result

    def test_label_in_timeline_start(self):
        result = str(Timeline(items=[TimelineItem(content="Content", label="2024-01")]))
        assert "timeline-start" in result
        assert "2024-01" in result

    def test_no_label(self):
        result = str(Timeline(items=[TimelineItem(content="Content")]))
        assert "timeline-start" not in result

    def test_content_in_timeline_end(self):
        result = str(Timeline(items=[TimelineItem(content="My Content")]))
        assert "timeline-end" in result
        assert "My Content" in result

    def test_timeline_middle_has_svg(self):
        result = str(Timeline(items=[TimelineItem(content="A")]))
        assert "timeline-middle" in result
        assert "<svg" in result

    def test_color_on_hr(self):
        result = str(Timeline(items=[
            TimelineItem(content="A", color="primary"),
            TimelineItem(content="B"),
        ]))
        assert "bg-primary" in result

    def test_color_on_icon(self):
        result = str(Timeline(items=[TimelineItem(content="A", color="success")]))
        assert "text-success" in result

    def test_first_item_no_leading_hr(self):
        result = str(Timeline(items=[
            TimelineItem(content="First"),
            TimelineItem(content="Second"),
        ]))
        # The first <li> should not start with <hr
        # Find the first <li> content
        first_li_start = result.index("<li>") + len("<li>")
        first_li_content = result[first_li_start:result.index("</li>")]
        # First element inside first <li> should not be <hr
        stripped = first_li_content.strip()
        assert not stripped.startswith("<hr")

    def test_last_item_no_trailing_hr(self):
        result = str(Timeline(items=[
            TimelineItem(content="First"),
            TimelineItem(content="Last"),
        ]))
        # Find the last </li> and check what precedes it
        last_li_end = result.rindex("</li>")
        last_li_start = result.rindex("<li>") + len("<li>")
        last_li_content = result[last_li_start:last_li_end]
        stripped = last_li_content.strip()
        assert not stripped.endswith("/>"), "Last item should not end with <hr />"

    def test_middle_item_has_both_hr(self):
        result = str(Timeline(items=[
            TimelineItem(content="A"),
            TimelineItem(content="B"),
            TimelineItem(content="C"),
        ]))
        # Count <hr elements - should be:
        # A: trailing hr (1)
        # B: leading hr + trailing hr (2)
        # C: leading hr (1)
        # Total = 4
        assert result.count("<hr") == 4

    def test_single_item_no_hr(self):
        result = str(Timeline(items=[TimelineItem(content="Only")]))
        assert "<hr" not in result

    def test_xss_escape(self):
        result = str(Timeline(items=[
            TimelineItem(content="<script>alert(1)</script>", label="<b>bad</b>"),
        ]))
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        assert "<b>" not in result
        assert "&lt;b&gt;" in result

    def test_custom_icon(self):
        result = str(Timeline(items=[
            TimelineItem(content="A", icon=Span("★", cls="text-xl")),
        ]))
        assert "★" in result
        # Should not contain the default SVG checkmark
        assert "fill-rule" not in result

    def test_empty_items(self):
        result = str(Timeline(items=[]))
        assert "<ul" in result
        assert "<li>" not in result

    def test_extra_attrs(self):
        result = str(Timeline(items=[TimelineItem(content="A")], id="my-timeline"))
        assert 'id="my-timeline"' in result

    def test_all_colors(self):
        for color in ["primary", "secondary", "accent", "info", "success", "warning", "error", "neutral"]:
            result = str(Timeline(items=[
                TimelineItem(content="A", color=color),
                TimelineItem(content="B"),
            ]))
            assert f"bg-{color}" in result
