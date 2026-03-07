"""Tests for InlineEdit component."""

from __future__ import annotations

from kokage_ui.htmx import InlineEdit


# ========================================
# TestInlineEdit — display mode
# ========================================


class TestInlineEdit:
    def test_basic_render(self):
        ie = InlineEdit("Alice", edit_url="/users/1/edit/name", name="name")
        html = ie.render()
        assert "<span>Alice</span>" in html
        assert "<button" in html

    def test_htmx_attributes(self):
        ie = InlineEdit("Alice", edit_url="/users/1/edit/name", name="name")
        html = ie.render()
        assert 'hx-get="/users/1/edit/name"' in html
        assert 'hx-target="closest div"' in html
        assert 'hx-swap="outerHTML"' in html

    def test_group_and_hover_classes(self):
        ie = InlineEdit("Alice", edit_url="/edit", name="name")
        html = ie.render()
        assert "group" in html
        assert "opacity-0" in html
        assert "group-hover:opacity-100" in html

    def test_custom_edit_label(self):
        ie = InlineEdit("Alice", edit_url="/edit", name="name", edit_label="Edit")
        html = ie.render()
        assert "Edit</button>" in html

    def test_xss_escape(self):
        ie = InlineEdit(
            '<script>alert("xss")</script>',
            edit_url="/edit",
            name="name",
        )
        html = ie.render()
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_renders_div_tag(self):
        ie = InlineEdit("Val", edit_url="/edit", name="f")
        html = ie.render()
        assert html.startswith("<div")
        assert html.endswith("</div>")


# ========================================
# TestInlineEditForm — edit mode
# ========================================


class TestInlineEditForm:
    def test_basic_render(self):
        form = InlineEdit.form(
            value="Alice",
            name="name",
            save_url="/users/1",
            cancel_url="/users/1/view/name",
        )
        html = form.render()
        assert "<form" in html
        assert "<input" in html
        assert "<button" in html

    def test_hidden_field_input(self):
        form = InlineEdit.form(
            value="Alice",
            name="name",
            save_url="/users/1",
            cancel_url="/users/1/view/name",
        )
        html = form.render()
        assert 'type="hidden"' in html
        assert 'name="_field"' in html
        assert 'value="name"' in html

    def test_htmx_attributes(self):
        form = InlineEdit.form(
            value="Alice",
            name="name",
            save_url="/users/1",
            cancel_url="/users/1/view/name",
        )
        html = form.render()
        assert 'hx-patch="/users/1"' in html
        assert 'hx-target="this"' in html
        assert 'hx-swap="outerHTML"' in html

    def test_value_in_input(self):
        form = InlineEdit.form(
            value="Alice",
            name="name",
            save_url="/users/1",
            cancel_url="/cancel",
        )
        html = form.render()
        assert 'value="Alice"' in html

    def test_cancel_button_hx_get(self):
        form = InlineEdit.form(
            value="Alice",
            name="name",
            save_url="/save",
            cancel_url="/users/1/view/name",
        )
        html = form.render()
        assert 'hx-get="/users/1/view/name"' in html
        assert 'hx-target="closest form"' in html

    def test_custom_input_type(self):
        form = InlineEdit.form(
            value="42",
            name="age",
            save_url="/save",
            cancel_url="/cancel",
            input_type="number",
        )
        html = form.render()
        assert 'type="number"' in html

    def test_custom_labels(self):
        form = InlineEdit.form(
            value="val",
            name="f",
            save_url="/save",
            cancel_url="/cancel",
            save_label="Save",
            cancel_label="Cancel",
        )
        html = form.render()
        assert "Save</button>" in html
        assert "Cancel</button>" in html

    def test_xss_escape(self):
        form = InlineEdit.form(
            value='<script>alert("xss")</script>',
            name="name",
            save_url="/save",
            cancel_url="/cancel",
        )
        html = form.render()
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_returns_form_element(self):
        form = InlineEdit.form(
            value="val",
            name="f",
            save_url="/save",
            cancel_url="/cancel",
        )
        html = form.render()
        assert html.startswith("<form")
        assert html.endswith("</form>")
