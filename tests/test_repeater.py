"""Tests for repeater field (dynamic add/remove form rows)."""

from __future__ import annotations

from typing import Annotated, Any
from unittest.mock import MagicMock

import pytest
import dataclasses

from pydantic import BaseModel

from kokage_ui.models import (
    _extract_repeater_field,
    _field_to_component,
    _render_value,
)
from kokage_ui.fields.repeater import RepeaterField, RepeaterInput


# ---- Test models ----


class TagModel(BaseModel):
    tags: Annotated[list[str], RepeaterField()] = []


class StepModel(BaseModel):
    steps: Annotated[list[str], RepeaterField(add_label="Add step", placeholder="Step...", min_items=1)] = []


class PlainModel(BaseModel):
    name: str = ""


class MaxModel(BaseModel):
    items: Annotated[list[str], RepeaterField(max_items=3)] = []


# ========================================
# TestRepeaterField
# ========================================


class TestRepeaterField:
    def test_defaults(self) -> None:
        rf = RepeaterField()
        assert rf.min_items == 0
        assert rf.max_items is None
        assert rf.placeholder == ""
        assert rf.add_label == "Add"

    def test_frozen(self) -> None:
        rf = RepeaterField()
        with pytest.raises(dataclasses.FrozenInstanceError):
            rf.min_items = 5  # type: ignore[misc]

    def test_custom_values(self) -> None:
        rf = RepeaterField(min_items=2, max_items=10, placeholder="Enter...", add_label="New")
        assert rf.min_items == 2
        assert rf.max_items == 10
        assert rf.placeholder == "Enter..."
        assert rf.add_label == "New"


# ========================================
# TestRepeaterInput
# ========================================


class TestRepeaterInput:
    def test_render_with_values(self) -> None:
        ri = RepeaterInput(name="tags", values=["a", "b", "c"])
        html = ri.render()
        assert html.count('name="tags"') >= 3
        assert 'value="a"' in html
        assert 'value="b"' in html
        assert 'value="c"' in html

    def test_same_name_attribute(self) -> None:
        ri = RepeaterInput(name="items", values=["x", "y"])
        html = ri.render()
        # All inputs should share the same name
        assert html.count('name="items"') >= 2

    def test_empty_values_with_min_items(self) -> None:
        ri = RepeaterInput(name="items", values=[], min_items=2)
        html = ri.render()
        # Should have 2 empty rows
        assert html.count("data-repeater-row") >= 2

    def test_placeholder(self) -> None:
        ri = RepeaterInput(name="tags", placeholder="Enter tag...")
        html = ri.render()
        assert 'placeholder="Enter tag..."' in html

    def test_add_label(self) -> None:
        ri = RepeaterInput(name="tags", add_label="Add tag")
        html = ri.render()
        assert "+ Add tag" in html

    def test_remove_button_exists(self) -> None:
        ri = RepeaterInput(name="tags", values=["a"])
        html = ri.render()
        assert "data-repeater-remove" in html
        assert "\u2715" in html

    def test_template_exists(self) -> None:
        ri = RepeaterInput(name="tags")
        html = ri.render()
        assert "<template" in html
        assert "</template>" in html

    def test_script_exists(self) -> None:
        ri = RepeaterInput(name="tags")
        html = ri.render()
        assert "<script>" in html
        assert "</script>" in html

    def test_max_items_in_js(self) -> None:
        ri = RepeaterInput(name="tags", max_items=5)
        html = ri.render()
        assert "maxItems=5" in html

    def test_max_items_null_when_none(self) -> None:
        ri = RepeaterInput(name="tags", max_items=None)
        html = ri.render()
        assert "maxItems=null" in html

    def test_xss_escape(self) -> None:
        ri = RepeaterInput(name="tags", values=['<script>alert("xss")</script>'])
        html = ri.render()
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_custom_repeater_id(self) -> None:
        ri = RepeaterInput(name="tags", repeater_id="my-repeater")
        html = ri.render()
        assert 'id="my-repeater-rows"' in html
        assert 'id="my-repeater-tmpl"' in html


# ========================================
# TestExtractRepeaterField
# ========================================


class TestExtractRepeaterField:
    def test_annotated_repeater_field(self) -> None:
        fi = TagModel.model_fields["tags"]
        result = _extract_repeater_field(fi)
        assert result is not None
        assert isinstance(result, RepeaterField)

    def test_plain_field_returns_none(self) -> None:
        fi = PlainModel.model_fields["name"]
        result = _extract_repeater_field(fi)
        assert result is None


# ========================================
# TestFieldToComponentRepeater
# ========================================


class TestFieldToComponentRepeater:
    def test_repeater_field_generates_repeater_input(self) -> None:
        fi = TagModel.model_fields["tags"]
        comp = _field_to_component("tags", fi)
        html = comp.render()
        assert "data-repeater-row" in html
        assert "<template" in html

    def test_repeater_field_with_values(self) -> None:
        fi = TagModel.model_fields["tags"]
        comp = _field_to_component("tags", fi, value=["foo", "bar"])
        html = comp.render()
        assert 'value="foo"' in html
        assert 'value="bar"' in html

    def test_repeater_field_with_min_items(self) -> None:
        fi = StepModel.model_fields["steps"]
        comp = _field_to_component("steps", fi)
        html = comp.render()
        # min_items=1 should produce at least 1 row
        assert "data-repeater-row" in html
        assert "Add step" in html
        assert 'placeholder="Step..."' in html


# ========================================
# TestProcessListFields
# ========================================


class TestProcessListFields:
    def test_getlist_collects_values(self) -> None:
        from kokage_ui.data.crud import _process_list_fields

        form_data = MagicMock()
        form_data.getlist.return_value = ["a", "b", "c"]

        raw_data: dict[str, Any] = {}
        _process_list_fields(TagModel, raw_data, form_data, [])
        assert raw_data["tags"] == ["a", "b", "c"]
        form_data.getlist.assert_called_with("tags")

    def test_exclude_skips_field(self) -> None:
        from kokage_ui.data.crud import _process_list_fields

        form_data = MagicMock()
        raw_data: dict[str, Any] = {}
        _process_list_fields(TagModel, raw_data, form_data, ["tags"])
        assert "tags" not in raw_data
        form_data.getlist.assert_not_called()

    def test_non_list_field_ignored(self) -> None:
        from kokage_ui.data.crud import _process_list_fields

        form_data = MagicMock()
        raw_data: dict[str, Any] = {"name": "test"}
        _process_list_fields(PlainModel, raw_data, form_data, [])
        assert raw_data["name"] == "test"
        form_data.getlist.assert_not_called()


# ========================================
# TestRenderValueList
# ========================================


class TestRenderValueList:
    def test_list_renders_badges(self) -> None:
        result = _render_value(["a", "b", "c"])
        html = result.render()
        assert "a" in html
        assert "b" in html
        assert "c" in html
        assert "badge" in html

    def test_empty_list_renders_dash(self) -> None:
        result = _render_value([])
        assert result == "-"

    def test_list_over_five_shows_plus(self) -> None:
        result = _render_value(["a", "b", "c", "d", "e", "f", "g"])
        html = result.render()
        assert "+2" in html


# ========================================
# TestMultiStepFormListHidden
# ========================================


class TestMultiStepFormListHidden:
    def test_list_values_as_multiple_hidden(self) -> None:
        from kokage_ui.features.forms import FormStep, MultiStepForm

        class MyModel(BaseModel):
            tags: list[str] = []
            name: str = ""

        form = MultiStepForm(
            MyModel,
            steps=[
                FormStep(title="Step 1", fields=["tags"]),
                FormStep(title="Step 2", fields=["name"]),
            ],
            current_step=1,
            validate_url="/validate",
            action="/submit",
            values={"tags": ["x", "y", "z"]},
        )
        html = form.render()
        # Should have 3 hidden inputs for tags
        assert html.count('name="tags"') == 3
        assert 'value="x"' in html
        assert 'value="y"' in html
        assert 'value="z"' in html

    def test_scalar_value_single_hidden(self) -> None:
        from kokage_ui.features.forms import FormStep, MultiStepForm

        class MyModel(BaseModel):
            name: str = ""
            email: str = ""

        form = MultiStepForm(
            MyModel,
            steps=[
                FormStep(title="Step 1", fields=["name"]),
                FormStep(title="Step 2", fields=["email"]),
            ],
            current_step=1,
            validate_url="/validate",
            action="/submit",
            values={"name": "Alice"},
        )
        html = form.render()
        assert html.count('name="name"') == 1
        assert 'value="Alice"' in html
