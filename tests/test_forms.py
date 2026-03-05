"""Tests for form & validation enhancements."""

from __future__ import annotations

from typing import Literal

import pytest
from pydantic import BaseModel, Field

from kokage_ui.components import DependentSelect, DropZone, FileUpload
from kokage_ui.forms import FormStep, MultiStepForm
from kokage_ui.htmx import DependentField
from kokage_ui.models import ValidatedModelForm, _build_form_input, _field_to_component, _SENTINEL


# ========================================
# Test models
# ========================================


class SimpleUser(BaseModel):
    username: str = Field(min_length=3)
    email: str
    age: int = Field(ge=0)


class RegistrationModel(BaseModel):
    username: str = Field(min_length=3)
    email: str
    age: int = Field(ge=0, default=18)
    bio: str = ""
    plan: Literal["free", "pro", "enterprise"] = "free"
    accept_terms: bool = False


# ========================================
# Feature 1: Real-time Validation
# ========================================


class TestBuildFormInputFieldId:
    """Test field_id parameter on _build_form_input."""

    def test_no_field_id(self):
        from kokage_ui.elements import Input

        el = Input(type="text", name="test")
        result = _build_form_input(label_text="Test", input_element=el)
        html = result.render()
        assert 'id="' not in html or 'id="field-' not in html

    def test_with_field_id(self):
        from kokage_ui.elements import Input

        el = Input(type="text", name="test")
        result = _build_form_input(label_text="Test", input_element=el, field_id="field-test")
        html = result.render()
        assert 'id="field-test"' in html


class TestFieldToComponentExtraAttrs:
    """Test extra_input_attrs and field_id on _field_to_component."""

    def test_extra_attrs_on_text_input(self):
        fi = SimpleUser.model_fields["username"]
        result = _field_to_component(
            "username",
            fi,
            extra_input_attrs={"hx_post": "/validate/username"},
            field_id="field-username",
        )
        html = result.render()
        assert 'hx-post="/validate/username"' in html
        assert 'id="field-username"' in html

    def test_extra_attrs_on_number_input(self):
        fi = SimpleUser.model_fields["age"]
        result = _field_to_component(
            "age",
            fi,
            extra_input_attrs={"hx_trigger": "change"},
            field_id="field-age",
        )
        html = result.render()
        assert 'hx-trigger="change"' in html
        assert 'id="field-age"' in html

    def test_no_extra_attrs(self):
        fi = SimpleUser.model_fields["username"]
        result = _field_to_component("username", fi)
        html = result.render()
        assert "hx-post" not in html
        assert 'id="field-' not in html

    def test_extra_attrs_on_bool_checkbox(self):
        fi = RegistrationModel.model_fields["accept_terms"]
        result = _field_to_component(
            "accept_terms",
            fi,
            extra_input_attrs={"hx_post": "/validate/accept_terms"},
            field_id="field-accept_terms",
        )
        html = result.render()
        assert 'hx-post="/validate/accept_terms"' in html
        assert 'id="field-accept_terms"' in html

    def test_extra_attrs_on_literal_select(self):
        fi = RegistrationModel.model_fields["plan"]
        result = _field_to_component(
            "plan",
            fi,
            extra_input_attrs={"hx_post": "/validate/plan"},
            field_id="field-plan",
        )
        html = result.render()
        assert 'hx-post="/validate/plan"' in html
        assert 'id="field-plan"' in html


class TestValidatedModelForm:
    """Test ValidatedModelForm."""

    def test_basic_render(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            action="/submit",
        )
        html = form.render()
        # Each field should have htmx validation attrs
        assert 'hx-post="/validate/username"' in html
        assert 'hx-post="/validate/email"' in html
        assert 'hx-post="/validate/age"' in html

    def test_field_id_wrappers(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            action="/submit",
        )
        html = form.render()
        assert 'id="field-username"' in html
        assert 'id="field-email"' in html
        assert 'id="field-age"' in html

    def test_trigger_delay(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            validate_trigger="input",
            validate_delay=300,
            action="/submit",
        )
        html = form.render()
        assert 'hx-trigger="input delay:300ms"' in html

    def test_no_delay(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            validate_delay=0,
            action="/submit",
        )
        html = form.render()
        assert 'hx-trigger="change"' in html

    def test_swap_target(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            action="/submit",
        )
        html = form.render()
        assert 'hx-target="#field-username"' in html
        assert 'hx-swap="outerHTML"' in html

    def test_with_errors(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            action="/submit",
            errors=[{"loc": ("username",), "msg": "Too short"}],
        )
        html = form.render()
        assert "Too short" in html

    def test_with_values(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            action="/submit",
            values={"username": "alice", "email": "a@b.com", "age": "25"},
        )
        html = form.render()
        assert 'value="alice"' in html

    def test_exclude_fields(self):
        form = ValidatedModelForm(
            SimpleUser,
            validate_url="/validate",
            action="/submit",
            exclude=["age"],
        )
        html = form.render()
        assert 'hx-post="/validate/username"' in html
        assert 'hx-post="/validate/age"' not in html


# ========================================
# Feature 2: File Upload
# ========================================


class TestFileUpload:
    """Test FileUpload component."""

    def test_basic(self):
        upload = FileUpload(name="avatar")
        html = upload.render()
        assert 'type="file"' in html
        assert 'name="avatar"' in html
        assert "file-input" in html

    def test_with_label(self):
        upload = FileUpload(name="avatar", label="Photo")
        html = upload.render()
        assert "Photo" in html

    def test_accept(self):
        upload = FileUpload(name="avatar", accept="image/*")
        html = upload.render()
        assert 'accept="image/*"' in html

    def test_multiple(self):
        upload = FileUpload(name="files", multiple=True)
        html = upload.render()
        assert "multiple" in html

    def test_color(self):
        upload = FileUpload(name="f", color="primary")
        html = upload.render()
        assert "file-input-primary" in html

    def test_size(self):
        upload = FileUpload(name="f", size="sm")
        html = upload.render()
        assert "file-input-sm" in html

    def test_bordered(self):
        upload = FileUpload(name="f", bordered=True)
        html = upload.render()
        assert "file-input-bordered" in html

    def test_no_border(self):
        upload = FileUpload(name="f", bordered=False)
        html = upload.render()
        assert "file-input-bordered" not in html


class TestDropZone:
    """Test DropZone component."""

    def test_basic(self):
        zone = DropZone(name="doc", upload_url="/upload")
        html = zone.render()
        assert 'hx-post="/upload"' in html
        assert 'hx-encoding="multipart/form-data"' in html
        assert 'type="file"' in html
        assert "border-dashed" in html

    def test_with_target(self):
        zone = DropZone(name="doc", upload_url="/upload", target="#preview")
        html = zone.render()
        assert 'hx-target="#preview"' in html

    def test_accept(self):
        zone = DropZone(name="doc", upload_url="/upload", accept=".pdf")
        html = zone.render()
        assert 'accept=".pdf"' in html

    def test_multiple(self):
        zone = DropZone(name="doc", upload_url="/upload", multiple=True)
        html = zone.render()
        assert "multiple" in html

    def test_custom_text(self):
        zone = DropZone(name="doc", upload_url="/upload", text="Upload here")
        html = zone.render()
        assert "Upload here" in html

    def test_trigger(self):
        zone = DropZone(name="doc", upload_url="/upload")
        html = zone.render()
        assert "change from:find input[type=file]" in html


# ========================================
# Feature 3: Dependent Fields
# ========================================


class TestDependentSelect:
    """Test DependentSelect component."""

    def test_basic(self):
        select = DependentSelect(
            name="city",
            depends_on="country",
            url="/api/cities",
        )
        html = select.render()
        assert 'name="city"' in html
        assert 'hx-get="/api/cities"' in html
        assert "change from:[name=&#39;country&#39;]" in html
        assert "[name=&#39;country&#39;]" in html

    def test_with_label(self):
        select = DependentSelect(
            name="city",
            depends_on="country",
            url="/api/cities",
            label="City",
        )
        html = select.render()
        assert "City" in html

    def test_placeholder(self):
        select = DependentSelect(
            name="city",
            depends_on="country",
            url="/api/cities",
            placeholder="Choose city...",
        )
        html = select.render()
        assert "Choose city..." in html

    def test_bordered(self):
        select = DependentSelect(
            name="city",
            depends_on="country",
            url="/api/cities",
            bordered=True,
        )
        html = select.render()
        assert "select-bordered" in html


class TestDependentField:
    """Test DependentField htmx component."""

    def test_basic(self):
        field = DependentField(
            "Loading...",
            depends_on="type",
            url="/api/options",
        )
        html = field.render()
        assert 'hx-get="/api/options"' in html
        assert "change from:[name=&#39;type&#39;]" in html
        assert "Loading..." in html

    def test_include(self):
        field = DependentField(
            depends_on="type",
            url="/api/options",
        )
        html = field.render()
        assert "[name=&#39;type&#39;]" in html

    def test_custom_swap(self):
        field = DependentField(
            depends_on="type",
            url="/api/options",
            swap="outerHTML",
        )
        html = field.render()
        assert 'hx-swap="outerHTML"' in html

    def test_with_target(self):
        field = DependentField(
            depends_on="type",
            url="/api/options",
            target="#container",
        )
        html = field.render()
        assert 'hx-target="#container"' in html


# ========================================
# Feature 4: Multi-step Form
# ========================================


class TestFormStep:
    """Test FormStep dataclass."""

    def test_basic(self):
        step = FormStep(title="Account", fields=["username", "email"])
        assert step.title == "Account"
        assert step.fields == ["username", "email"]
        assert step.description == ""

    def test_with_description(self):
        step = FormStep(
            title="Profile",
            fields=["age", "bio"],
            description="Tell us about yourself",
        )
        assert step.description == "Tell us about yourself"


class TestMultiStepForm:
    """Test MultiStepForm component."""

    def _make_steps(self):
        return [
            FormStep("Account", ["username", "email"]),
            FormStep("Profile", ["age", "bio"]),
            FormStep("Plan", ["plan", "accept_terms"]),
        ]

    def test_renders_progress(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert "steps" in html
        assert "Account" in html
        assert "Profile" in html
        assert "Plan" in html

    def test_step_0_fields(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert 'name="username"' in html
        assert 'name="email"' in html
        # Step 1 fields should not be visible (not as form inputs)
        assert 'name="bio"' not in html

    def test_step_1_fields(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=1,
            validate_url="/register/step",
            action="/register/submit",
            values={"username": "alice", "email": "a@b.com"},
        )
        html = form.render()
        assert 'name="age"' in html
        assert 'name="bio"' in html

    def test_hidden_fields_for_previous_steps(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=1,
            validate_url="/register/step",
            action="/register/submit",
            values={"username": "alice", "email": "a@b.com"},
        )
        html = form.render()
        assert 'type="hidden"' in html
        assert 'value="alice"' in html
        assert 'value="a@b.com"' in html

    def test_next_button(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert "Next" in html
        assert 'hx-post="/register/step/0"' in html
        assert "Submit" not in html

    def test_previous_button(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=1,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert "Previous" in html
        assert 'hx-post="/register/step/goto/0"' in html

    def test_no_previous_on_first_step(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert "Previous" not in html

    def test_submit_on_last_step(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=2,
            validate_url="/register/step",
            action="/register/submit",
            values={"username": "alice", "email": "a@b.com", "age": "25", "bio": "hi"},
        )
        html = form.render()
        assert "Submit" in html
        assert "Next" not in html

    def test_errors_display(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
            errors=[{"loc": ("username",), "msg": "Too short"}],
        )
        html = form.render()
        assert "Too short" in html

    def test_form_id(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert 'id="multistep-form"' in html

    def test_htmx_targets_form(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert 'hx-target="#multistep-form"' in html

    def test_step_description(self):
        steps = [
            FormStep("Account", ["username", "email"], description="Create your account"),
            FormStep("Profile", ["age", "bio"]),
        ]
        form = MultiStepForm(
            RegistrationModel,
            steps=steps,
            current_step=0,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert "Create your account" in html

    def test_form_action(self):
        form = MultiStepForm(
            RegistrationModel,
            steps=self._make_steps(),
            current_step=2,
            validate_url="/register/step",
            action="/register/submit",
        )
        html = form.render()
        assert 'action="/register/submit"' in html


# ========================================
# Integration: core.py validate/multistep
# ========================================


class TestKokageUIValidate:
    """Test KokageUI.validate() endpoint registration."""

    def test_registers_validation_endpoints(self):
        from fastapi import FastAPI

        from kokage_ui.core import KokageUI

        app = FastAPI()
        ui = KokageUI(app)
        ui.validate("/validate", SimpleUser)

        routes = [r.path for r in app.routes]
        assert "/validate/username" in routes
        assert "/validate/email" in routes
        assert "/validate/age" in routes

    def test_exclude_fields(self):
        from fastapi import FastAPI

        from kokage_ui.core import KokageUI

        app = FastAPI()
        ui = KokageUI(app)
        ui.validate("/validate", SimpleUser, exclude=["age"])

        routes = [r.path for r in app.routes]
        assert "/validate/username" in routes
        assert "/validate/email" in routes
        assert "/validate/age" not in routes


class TestKokageUIMultistep:
    """Test KokageUI.multistep() endpoint registration."""

    def test_registers_step_endpoints(self):
        from fastapi import FastAPI

        from kokage_ui.core import KokageUI

        app = FastAPI()
        ui = KokageUI(app)

        steps = [
            FormStep("Account", ["username", "email"]),
            FormStep("Profile", ["age"]),
        ]
        ui.multistep(
            "/register/step",
            model=SimpleUser,
            steps=steps,
            action="/register/submit",
        )

        routes = [r.path for r in app.routes]
        assert "/register/step/{step}" in routes
        assert "/register/step/goto/{step}" in routes


# ========================================
# Integration: CRUDRouter with validation
# ========================================


class TestCRUDRouterValidation:
    """Test CRUDRouter with realtime_validation=True."""

    def test_registers_validation_routes(self):
        from fastapi import FastAPI

        from kokage_ui.crud import CRUDRouter, InMemoryStorage

        class Item(BaseModel):
            id: str = ""
            name: str
            price: int = 0

        app = FastAPI()
        storage = InMemoryStorage(Item)
        CRUDRouter(
            app,
            "/items",
            Item,
            storage,
            realtime_validation=True,
        )

        routes = [r.path for r in app.routes]
        assert "/items/_validate/name" in routes
        assert "/items/_validate/price" in routes
        # id is excluded from forms, so no validation route for it
        assert "/items/_validate/id" not in routes

    def test_no_validation_routes_by_default(self):
        from fastapi import FastAPI

        from kokage_ui.crud import CRUDRouter, InMemoryStorage

        class Item(BaseModel):
            id: str = ""
            name: str
            price: int = 0

        app = FastAPI()
        storage = InMemoryStorage(Item)
        CRUDRouter(app, "/items", Item, storage)

        routes = [r.path for r in app.routes]
        assert "/items/_validate/name" not in routes


# ========================================
# Import test
# ========================================


class TestImports:
    """Test that all new symbols are importable."""

    def test_import_all(self):
        from kokage_ui import (
            DependentField,
            DependentSelect,
            DropZone,
            FileUpload,
            FormStep,
            MultiStepForm,
            ValidatedModelForm,
        )

        assert ValidatedModelForm is not None
        assert FileUpload is not None
        assert DropZone is not None
        assert DependentSelect is not None
        assert DependentField is not None
        assert FormStep is not None
        assert MultiStepForm is not None
