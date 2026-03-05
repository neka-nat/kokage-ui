"""Multi-step form support.

Provides FormStep and MultiStepForm for building wizard-style forms
that split model fields across multiple steps with htmx navigation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from kokage_ui.components import Step, Steps
from kokage_ui.elements import Button, Component, Div, Form, Input, P
from kokage_ui.models import _SENTINEL, _field_to_component


@dataclass
class FormStep:
    """Definition of a single step in a multi-step form.

    Args:
        title: Step title (shown in progress indicator).
        fields: List of model field names for this step.
        description: Optional description text.
    """

    title: str
    fields: list[str]
    description: str = ""


class MultiStepForm(Component):
    """Multi-step form with progress indicator and htmx navigation.

    Splits model fields across steps with Previous/Next buttons.
    Previous steps' values are preserved as hidden inputs.

    Args:
        model: Pydantic BaseModel class.
        steps: List of FormStep definitions.
        current_step: 0-indexed current step.
        validate_url: Base URL for step validation/navigation endpoints.
        action: Form action URL for final submission.
        values: Dict of field values (from previous steps and current).
        errors: List of Pydantic ValidationError dicts for inline errors.
    """

    tag = "div"

    def __init__(
        self,
        model: type[BaseModel],
        *,
        steps: list[FormStep],
        current_step: int = 0,
        validate_url: str,
        action: str,
        values: dict[str, Any] | None = None,
        errors: list[dict[str, Any]] | None = None,
        **attrs: Any,
    ) -> None:
        values = values or {}

        # Build progress indicator
        step_items = [Step(label=s.title) for s in steps]
        progress = Steps(steps=step_items, current=current_step)

        # Build error map
        error_map: dict[str, str] = {}
        if errors:
            for err in errors:
                loc = err.get("loc", ())
                if loc:
                    field_name = str(loc[0])
                    if field_name not in error_map:
                        error_map[field_name] = err.get("msg", "Invalid value")

        # Current step's fields
        current = steps[current_step]
        field_components: list[Any] = []

        if current.description:
            field_components.append(P(current.description, cls="text-base-content/70 mb-2"))

        for field_name in current.fields:
            if field_name in model.model_fields:
                fi = model.model_fields[field_name]
                val = values.get(field_name, _SENTINEL)
                field_components.append(
                    _field_to_component(
                        field_name,
                        fi,
                        value=val,
                        error_message=error_map.get(field_name),
                    )
                )

        # Hidden fields for previous steps' values
        hidden_fields: list[Any] = []
        for i in range(current_step):
            for field_name in steps[i].fields:
                if field_name in values:
                    val = values[field_name]
                    if isinstance(val, list):
                        for item in val:
                            hidden_fields.append(
                                Input(type="hidden", name=field_name, value=str(item))
                            )
                    else:
                        hidden_fields.append(
                            Input(type="hidden", name=field_name, value=str(val))
                        )

        # Navigation buttons
        nav_buttons: list[Any] = []
        if current_step > 0:
            nav_buttons.append(
                Button(
                    "Previous",
                    type="button",
                    cls="btn btn-ghost",
                    hx_post=f"{validate_url}/goto/{current_step - 1}",
                    hx_target="#multistep-form",
                    hx_swap="outerHTML",
                )
            )

        if current_step < len(steps) - 1:
            nav_buttons.append(
                Button(
                    "Next",
                    type="button",
                    cls="btn btn-primary",
                    hx_post=f"{validate_url}/{current_step}",
                    hx_target="#multistep-form",
                    hx_swap="outerHTML",
                )
            )
        else:
            nav_buttons.append(
                Button("Submit", type="submit", cls="btn btn-primary")
            )

        form = Form(
            *hidden_fields,
            *field_components,
            Div(*nav_buttons, cls="flex justify-between mt-4"),
            action=action,
            method="post",
        )

        attrs.setdefault("id", "multistep-form")
        super().__init__(progress, form, **attrs)
