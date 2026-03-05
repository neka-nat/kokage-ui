"""Tests for Pydantic model → UI auto-generation."""

import enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from kokage_ui.models import (
    FieldConstraints,
    ModelDetail,
    ModelForm,
    ModelTable,
    _extract_constraints,
    _field_to_component,
    _resolve_annotation,
)


# ---- Test models ----


class Role(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class UserForm(BaseModel):
    name: str
    email: str
    age: int = Field(ge=0, le=150)
    bio: str = Field(default="", max_length=500)
    password: str
    is_active: bool = True
    role: Role = Role.VIEWER
    status: Literal["draft", "published", "archived"] = "draft"


class SimpleModel(BaseModel):
    title: str
    count: int


class ConstrainedModel(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-z]+$")
    score: float = Field(gt=0, lt=100)
    level: int = Field(ge=1, le=10)


# ========================================
# _resolve_annotation tests
# ========================================


class TestResolveAnnotation:
    def test_str(self):
        base, is_opt = _resolve_annotation(str)
        assert base is str
        assert is_opt is False

    def test_int(self):
        base, is_opt = _resolve_annotation(int)
        assert base is int
        assert is_opt is False

    def test_bool(self):
        base, is_opt = _resolve_annotation(bool)
        assert base is bool
        assert is_opt is False

    def test_optional_str(self):
        base, is_opt = _resolve_annotation(Optional[str])
        assert base is str
        assert is_opt is True

    def test_union_none(self):
        base, is_opt = _resolve_annotation(str | None)
        assert base is str
        assert is_opt is True

    def test_literal(self):
        ann = Literal["a", "b", "c"]
        base, is_opt = _resolve_annotation(ann)
        assert base is ann
        assert is_opt is False


# ========================================
# _extract_constraints tests
# ========================================


class TestExtractConstraints:
    def test_min_max_length(self):
        fi = ConstrainedModel.model_fields["username"]
        c = _extract_constraints(fi)
        assert c.min_length == 3
        assert c.max_length == 20

    def test_pattern(self):
        fi = ConstrainedModel.model_fields["username"]
        c = _extract_constraints(fi)
        assert c.pattern == r"^[a-z]+$"

    def test_gt_lt(self):
        fi = ConstrainedModel.model_fields["score"]
        c = _extract_constraints(fi)
        assert c.gt == 0
        assert c.lt == 100

    def test_ge_le(self):
        fi = ConstrainedModel.model_fields["level"]
        c = _extract_constraints(fi)
        assert c.ge == 1
        assert c.le == 10

    def test_no_constraints(self):
        fi = SimpleModel.model_fields["title"]
        c = _extract_constraints(fi)
        assert c == FieldConstraints()


# ========================================
# _field_to_component tests
# ========================================


class TestFieldToComponent:
    def test_str_field_text_input(self):
        fi = SimpleModel.model_fields["title"]
        result = str(_field_to_component("title", fi))
        assert 'type="text"' in result
        assert 'name="title"' in result

    def test_int_field_number_input(self):
        fi = SimpleModel.model_fields["count"]
        result = str(_field_to_component("count", fi))
        assert 'type="number"' in result
        assert 'step="1"' in result

    def test_float_field_number_input(self):
        fi = ConstrainedModel.model_fields["score"]
        result = str(_field_to_component("score", fi))
        assert 'type="number"' in result
        assert 'step="any"' in result

    def test_bool_field_checkbox(self):
        fi = UserForm.model_fields["is_active"]
        result = str(_field_to_component("is_active", fi))
        assert 'type="checkbox"' in result
        assert "checkbox" in result

    def test_email_heuristic(self):
        fi = UserForm.model_fields["email"]
        result = str(_field_to_component("email", fi))
        assert 'type="email"' in result

    def test_password_heuristic(self):
        fi = UserForm.model_fields["password"]
        result = str(_field_to_component("password", fi))
        assert 'type="password"' in result

    def test_bio_textarea_heuristic(self):
        fi = UserForm.model_fields["bio"]
        result = str(_field_to_component("bio", fi))
        assert "<textarea" in result

    def test_literal_select(self):
        fi = UserForm.model_fields["status"]
        result = str(_field_to_component("status", fi))
        assert "<select" in result
        assert "draft" in result
        assert "published" in result
        assert "archived" in result

    def test_enum_select(self):
        fi = UserForm.model_fields["role"]
        result = str(_field_to_component("role", fi))
        assert "<select" in result
        assert "ADMIN" in result
        assert "EDITOR" in result

    def test_required_attribute(self):
        fi = SimpleModel.model_fields["title"]
        result = str(_field_to_component("title", fi))
        assert " required" in result

    def test_default_value(self):
        fi = UserForm.model_fields["status"]
        result = str(_field_to_component("status", fi))
        assert "selected" in result

    def test_constraints_on_str(self):
        fi = ConstrainedModel.model_fields["username"]
        result = str(_field_to_component("username", fi))
        assert 'minlength="3"' in result
        assert 'maxlength="20"' in result
        assert 'pattern="^[a-z]+$"' in result

    def test_constraints_ge_le(self):
        fi = ConstrainedModel.model_fields["level"]
        result = str(_field_to_component("level", fi))
        assert 'min="1"' in result
        assert 'max="10"' in result

    def test_constraints_gt_lt(self):
        fi = ConstrainedModel.model_fields["score"]
        result = str(_field_to_component("score", fi))
        assert 'min="0"' in result
        assert 'max="100"' in result


# ========================================
# ModelForm tests
# ========================================


class TestModelForm:
    def test_form_tag(self):
        result = str(ModelForm(SimpleModel))
        assert "<form" in result
        assert "</form>" in result

    def test_form_action_method(self):
        result = str(ModelForm(SimpleModel, action="/submit", method="post"))
        assert 'action="/submit"' in result
        assert 'method="post"' in result

    def test_form_contains_all_fields(self):
        result = str(ModelForm(SimpleModel))
        assert 'name="title"' in result
        assert 'name="count"' in result

    def test_form_submit_button(self):
        result = str(ModelForm(SimpleModel))
        assert "Submit" in result
        assert "btn" in result

    def test_form_custom_submit(self):
        result = str(ModelForm(SimpleModel, submit_text="Save", submit_color="success"))
        assert "Save" in result
        assert "btn-success" in result

    def test_form_exclude(self):
        result = str(ModelForm(SimpleModel, exclude=["count"]))
        assert 'name="title"' in result
        assert 'name="count"' not in result

    def test_form_include(self):
        result = str(ModelForm(SimpleModel, include=["title"]))
        assert 'name="title"' in result
        assert 'name="count"' not in result

    def test_form_full_model(self):
        result = str(ModelForm(UserForm))
        assert 'name="name"' in result
        assert 'name="email"' in result
        assert 'type="email"' in result
        assert 'type="checkbox"' in result
        assert "<select" in result


# ========================================
# ModelTable tests
# ========================================


class TestModelTable:
    def _sample_rows(self):
        return [
            SimpleModel(title="First", count=1),
            SimpleModel(title="Second", count=2),
        ]

    def test_table_headers(self):
        result = str(ModelTable(SimpleModel, rows=self._sample_rows()))
        assert "<th>Title</th>" in result
        assert "<th>Count</th>" in result

    def test_table_data(self):
        result = str(ModelTable(SimpleModel, rows=self._sample_rows()))
        assert "First" in result
        assert "Second" in result

    def test_table_bool_badge(self):
        rows = [UserForm(name="A", email="a@b.com", age=25, password="x")]
        result = str(ModelTable(UserForm, rows=rows))
        assert "badge-success" in result
        assert "Active" in result

    def test_table_exclude(self):
        result = str(ModelTable(SimpleModel, rows=self._sample_rows(), exclude=["count"]))
        assert "<th>Title</th>" in result
        assert "<th>Count</th>" not in result

    def test_table_zebra(self):
        result = str(ModelTable(SimpleModel, rows=self._sample_rows(), zebra=True))
        assert "table-zebra" in result

    def test_table_compact(self):
        result = str(ModelTable(SimpleModel, rows=self._sample_rows(), compact=True))
        assert "table-xs" in result

    def test_table_cell_renderers(self):
        renderers = {"title": lambda v: f"** {v} **"}
        result = str(ModelTable(SimpleModel, rows=self._sample_rows(), cell_renderers=renderers))
        assert "** First **" in result

    def test_table_empty_rows(self):
        result = str(ModelTable(SimpleModel, rows=[]))
        assert "<th>Title</th>" in result
        assert "<td>" not in result

    def test_extra_columns_basic(self):
        rows = self._sample_rows()
        result = str(
            ModelTable(
                SimpleModel,
                rows=rows,
                extra_columns={"Actions": lambda row: f"act-{row.title}"},
            )
        )
        assert "<th>Actions</th>" in result
        assert "act-First" in result
        assert "act-Second" in result

    def test_extra_columns_header_order(self):
        rows = self._sample_rows()
        result = str(
            ModelTable(
                SimpleModel,
                rows=rows,
                extra_columns={"Extra": lambda row: "x"},
            )
        )
        # Extra header should appear after model field headers
        title_pos = result.index("<th>Title</th>")
        count_pos = result.index("<th>Count</th>")
        extra_pos = result.index("<th>Extra</th>")
        assert title_pos < count_pos < extra_pos

    def test_extra_columns_empty_dict(self):
        rows = self._sample_rows()
        result_without = str(ModelTable(SimpleModel, rows=rows))
        result_with = str(ModelTable(SimpleModel, rows=rows, extra_columns={}))
        assert result_without == result_with


# ========================================
# ModelDetail tests
# ========================================


class TestModelDetail:
    def test_detail_card(self):
        instance = SimpleModel(title="Hello", count=42)
        result = str(ModelDetail(instance))
        assert "card" in result

    def test_detail_title_default(self):
        instance = SimpleModel(title="Hello", count=42)
        result = str(ModelDetail(instance))
        assert "SimpleModel" in result

    def test_detail_custom_title(self):
        instance = SimpleModel(title="Hello", count=42)
        result = str(ModelDetail(instance, title="Item Details"))
        assert "Item Details" in result

    def test_detail_values(self):
        instance = SimpleModel(title="Hello", count=42)
        result = str(ModelDetail(instance))
        assert "Hello" in result
        assert "42" in result

    def test_detail_bool_badge(self):
        instance = UserForm(name="A", email="a@b.com", age=25, password="x")
        result = str(ModelDetail(instance))
        assert "badge-success" in result
        assert "Active" in result

    def test_detail_exclude(self):
        instance = SimpleModel(title="Hello", count=42)
        result = str(ModelDetail(instance, exclude=["count"]))
        assert "Hello" in result
        assert "Count" not in result
