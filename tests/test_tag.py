"""Tests for tag input field (chip-based tag entry)."""

from __future__ import annotations

from typing import Annotated, Any
from unittest.mock import MagicMock

import pytest
import dataclasses

from pydantic import BaseModel

from kokage_ui.models import (
    _extract_tag_field,
    _field_to_component,
)
from kokage_ui.fields.tag import TagField, TagInput


# ---- Test models ----


class TagModel(BaseModel):
    tags: Annotated[list[str], TagField()] = []


class CustomTagModel(BaseModel):
    categories: Annotated[list[str], TagField(
        placeholder="カテゴリ...",
        max_tags=5,
        allow_duplicates=True,
        separator=";",
        color="secondary",
    )] = []


class PlainModel(BaseModel):
    name: str = ""


# ========================================
# TestTagField
# ========================================


class TestTagField:
    def test_defaults(self) -> None:
        tf = TagField()
        assert tf.placeholder == "タグを入力..."
        assert tf.max_tags is None
        assert tf.allow_duplicates is False
        assert tf.separator == ","
        assert tf.color == "primary"

    def test_custom_values(self) -> None:
        tf = TagField(
            placeholder="Enter...",
            max_tags=10,
            allow_duplicates=True,
            separator=";",
            color="accent",
        )
        assert tf.placeholder == "Enter..."
        assert tf.max_tags == 10
        assert tf.allow_duplicates is True
        assert tf.separator == ";"
        assert tf.color == "accent"

    def test_frozen(self) -> None:
        tf = TagField()
        with pytest.raises(dataclasses.FrozenInstanceError):
            tf.placeholder = "new"  # type: ignore[misc]


# ========================================
# TestTagInput render
# ========================================


class TestTagInput:
    def test_render_with_values(self) -> None:
        ti = TagInput(name="tags", values=["python", "rust", "go"])
        html = ti.render()
        assert "python" in html
        assert "rust" in html
        assert "go" in html

    def test_badge_class(self) -> None:
        ti = TagInput(name="tags", values=["a"], color="secondary")
        html = ti.render()
        assert "badge-secondary" in html

    def test_default_badge_color(self) -> None:
        ti = TagInput(name="tags", values=["a"])
        html = ti.render()
        assert "badge-primary" in html

    def test_hidden_inputs(self) -> None:
        ti = TagInput(name="tags", values=["x", "y"])
        html = ti.render()
        assert html.count('type="hidden"') == 2
        assert html.count('name="tags"') == 2
        assert 'value="x"' in html
        assert 'value="y"' in html

    def test_text_input_exists(self) -> None:
        ti = TagInput(name="tags")
        html = ti.render()
        assert 'type="text"' in html

    def test_placeholder(self) -> None:
        ti = TagInput(name="tags", placeholder="Add tag...")
        html = ti.render()
        assert 'placeholder="Add tag..."' in html

    def test_script_exists(self) -> None:
        ti = TagInput(name="tags")
        html = ti.render()
        assert "<script>" in html
        assert "</script>" in html

    def test_remove_button(self) -> None:
        ti = TagInput(name="tags", values=["a"])
        html = ti.render()
        assert "\u2715" in html

    def test_xss_escape(self) -> None:
        ti = TagInput(name="tags", values=['<script>alert("xss")</script>'])
        html = ti.render()
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_max_tags_in_js(self) -> None:
        ti = TagInput(name="tags", max_tags=3)
        html = ti.render()
        assert "maxTags=3" in html

    def test_max_tags_null_when_none(self) -> None:
        ti = TagInput(name="tags", max_tags=None)
        html = ti.render()
        assert "maxTags=null" in html

    def test_allow_duplicates_true(self) -> None:
        ti = TagInput(name="tags", allow_duplicates=True)
        html = ti.render()
        assert "allowDup=true" in html

    def test_allow_duplicates_false(self) -> None:
        ti = TagInput(name="tags", allow_duplicates=False)
        html = ti.render()
        assert "allowDup=false" in html

    def test_empty_values(self) -> None:
        ti = TagInput(name="tags", values=[])
        html = ti.render()
        # No badge spans rendered (chip string only in JS)
        assert "badge-primary" not in html.split("<script>")[0]
        assert 'type="text"' in html

    def test_custom_input_id(self) -> None:
        ti = TagInput(name="tags", input_id="my-tags")
        html = ti.render()
        assert 'id="my-tags-tags"' in html
        assert 'id="my-tags-input"' in html


# ========================================
# TestExtractTagField
# ========================================


class TestExtractTagField:
    def test_annotated_tag_field(self) -> None:
        fi = TagModel.model_fields["tags"]
        result = _extract_tag_field(fi)
        assert result is not None
        assert isinstance(result, TagField)

    def test_plain_field_returns_none(self) -> None:
        fi = PlainModel.model_fields["name"]
        result = _extract_tag_field(fi)
        assert result is None

    def test_custom_tag_field(self) -> None:
        fi = CustomTagModel.model_fields["categories"]
        result = _extract_tag_field(fi)
        assert result is not None
        assert result.max_tags == 5
        assert result.color == "secondary"


# ========================================
# TestFieldToComponentTag
# ========================================


class TestFieldToComponentTag:
    def test_tag_field_generates_tag_input(self) -> None:
        fi = TagModel.model_fields["tags"]
        comp = _field_to_component("tags", fi)
        html = comp.render()
        # No badge spans before <script> (no tags initially)
        assert "badge-primary" not in html.split("<script>")[0]
        assert 'type="text"' in html
        assert "<script>" in html

    def test_tag_field_with_values(self) -> None:
        fi = TagModel.model_fields["tags"]
        comp = _field_to_component("tags", fi, value=["foo", "bar"])
        html = comp.render()
        assert "foo" in html
        assert "bar" in html
        assert "badge-primary" in html
        assert html.count('type="hidden"') == 2

    def test_tag_field_custom_color(self) -> None:
        fi = CustomTagModel.model_fields["categories"]
        comp = _field_to_component("categories", fi, value=["a"])
        html = comp.render()
        assert "badge-secondary" in html


# ========================================
# TestProcessListFieldsTag
# ========================================


class TestProcessListFieldsTag:
    def test_getlist_collects_values(self) -> None:
        from kokage_ui.data.crud import _process_list_fields

        form_data = MagicMock()
        form_data.getlist.return_value = ["python", "rust", "go"]

        raw_data: dict[str, Any] = {}
        _process_list_fields(TagModel, raw_data, form_data, [])
        assert raw_data["tags"] == ["python", "rust", "go"]
        form_data.getlist.assert_called_with("tags")

    def test_exclude_skips_field(self) -> None:
        from kokage_ui.data.crud import _process_list_fields

        form_data = MagicMock()
        raw_data: dict[str, Any] = {}
        _process_list_fields(TagModel, raw_data, form_data, ["tags"])
        assert "tags" not in raw_data
        form_data.getlist.assert_not_called()
