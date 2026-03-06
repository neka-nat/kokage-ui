"""Tests for date/time picker support (flatpickr)."""

from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Annotated

import pytest
from pydantic import BaseModel

from kokage_ui.fields.datetime import DateField, DateTimeField, DateTimePicker, TimeField
from kokage_ui.models import (
    ModelForm,
    _extract_datetime_field,
    _field_to_component,
)
from kokage_ui.page import FLATPICKR_CSS_CDN, FLATPICKR_JS_CDN, Page


# --- TestDateField ---


class TestDateField:
    def test_defaults(self):
        f = DateField()
        assert f.format == "Y-m-d"
        assert f.min_date is None
        assert f.max_date is None
        assert f.placeholder == ""

    def test_custom_values(self):
        f = DateField(format="d/m/Y", min_date="2024-01-01", max_date="2025-12-31", placeholder="Select date")
        assert f.format == "d/m/Y"
        assert f.min_date == "2024-01-01"
        assert f.max_date == "2025-12-31"
        assert f.placeholder == "Select date"

    def test_frozen(self):
        f = DateField()
        with pytest.raises(dataclasses.FrozenInstanceError):
            f.format = "d/m/Y"  # type: ignore[misc]


# --- TestTimeField ---


class TestTimeField:
    def test_defaults(self):
        f = TimeField()
        assert f.format == "H:i"
        assert f.enable_seconds is False
        assert f.time_24hr is True
        assert f.placeholder == ""

    def test_custom_values(self):
        f = TimeField(format="h:i K", enable_seconds=True, time_24hr=False, placeholder="Pick time")
        assert f.format == "h:i K"
        assert f.enable_seconds is True
        assert f.time_24hr is False
        assert f.placeholder == "Pick time"

    def test_frozen(self):
        f = TimeField()
        with pytest.raises(dataclasses.FrozenInstanceError):
            f.format = "h:i"  # type: ignore[misc]


# --- TestDateTimeField ---


class TestDateTimeField:
    def test_defaults(self):
        f = DateTimeField()
        assert f.format == "Y-m-d H:i"
        assert f.enable_time is True
        assert f.time_24hr is True
        assert f.min_date is None
        assert f.max_date is None
        assert f.placeholder == ""

    def test_custom_values(self):
        f = DateTimeField(
            format="Y/m/d H:i:S",
            enable_time=False,
            time_24hr=False,
            min_date="2024-01-01",
            max_date="2025-12-31",
            placeholder="Select datetime",
        )
        assert f.format == "Y/m/d H:i:S"
        assert f.enable_time is False
        assert f.time_24hr is False
        assert f.min_date == "2024-01-01"
        assert f.max_date == "2025-12-31"
        assert f.placeholder == "Select datetime"

    def test_frozen(self):
        f = DateTimeField()
        with pytest.raises(dataclasses.FrozenInstanceError):
            f.format = "d/m/Y"  # type: ignore[misc]


# --- TestDateTimePicker ---


class TestDateTimePicker:
    def test_render_date_field(self):
        picker = DateTimePicker(
            name="start_date",
            value="2024-06-15",
            field_config=DateField(),
            picker_id="test-date",
        )
        html = picker.render()
        assert 'type="text"' in html
        assert 'id="test-date"' in html
        assert 'name="start_date"' in html
        assert 'value="2024-06-15"' in html
        assert "input input-bordered w-full" in html
        assert "<script>" in html
        assert "flatpickr" in html
        assert '"dateFormat":"Y-m-d"' in html

    def test_render_time_field(self):
        picker = DateTimePicker(
            name="start_time",
            field_config=TimeField(),
            picker_id="test-time",
        )
        html = picker.render()
        assert '"noCalendar":true' in html
        assert '"enableTime":true' in html
        assert '"time_24hr":true' in html

    def test_render_time_field_with_seconds(self):
        picker = DateTimePicker(
            name="precise_time",
            field_config=TimeField(enable_seconds=True),
            picker_id="test-time-sec",
        )
        html = picker.render()
        assert '"enableSeconds":true' in html

    def test_render_datetime_field(self):
        picker = DateTimePicker(
            name="starts_at",
            field_config=DateTimeField(),
            picker_id="test-datetime",
        )
        html = picker.render()
        assert '"enableTime":true' in html
        assert '"time_24hr":true' in html
        assert '"dateFormat":"Y-m-d H:i"' in html

    def test_render_date_field_with_min_max(self):
        picker = DateTimePicker(
            name="date",
            field_config=DateField(min_date="2024-01-01", max_date="2024-12-31"),
            picker_id="test-minmax",
        )
        html = picker.render()
        assert '"minDate":"2024-01-01"' in html
        assert '"maxDate":"2024-12-31"' in html

    def test_render_with_placeholder(self):
        picker = DateTimePicker(
            name="date",
            field_config=DateField(placeholder="Choose a date"),
            picker_id="test-ph",
        )
        html = picker.render()
        assert 'placeholder="Choose a date"' in html

    def test_auto_generated_id(self):
        picker = DateTimePicker(name="date", field_config=DateField())
        html = picker.render()
        assert "kokage-fp-" in html

    def test_library_guard(self):
        picker = DateTimePicker(name="date", picker_id="test-guard")
        html = picker.render()
        assert "if(typeof flatpickr==='undefined')" in html
        assert "console.error" in html


# --- TestExtractDatetimeField ---


class TestExtractDatetimeField:
    def test_extract_date_field(self):
        class M(BaseModel):
            d: Annotated[str, DateField()] = ""

        fi = M.model_fields["d"]
        result = _extract_datetime_field(fi)
        assert result is not None
        assert isinstance(result, DateField)

    def test_extract_time_field(self):
        class M(BaseModel):
            t: Annotated[str, TimeField()] = ""

        fi = M.model_fields["t"]
        result = _extract_datetime_field(fi)
        assert result is not None
        assert isinstance(result, TimeField)

    def test_extract_datetime_field(self):
        class M(BaseModel):
            dt: Annotated[str, DateTimeField()] = ""

        fi = M.model_fields["dt"]
        result = _extract_datetime_field(fi)
        assert result is not None
        assert isinstance(result, DateTimeField)

    def test_extract_returns_none_for_plain_field(self):
        class M(BaseModel):
            name: str = ""

        fi = M.model_fields["name"]
        result = _extract_datetime_field(fi)
        assert result is None


# --- TestFieldToComponentDatetime ---


class TestFieldToComponentDatetime:
    def test_date_field_generates_picker(self):
        class M(BaseModel):
            event_date: Annotated[str, DateField()] = ""

        fi = M.model_fields["event_date"]
        comp = _field_to_component("event_date", fi)
        html = comp.render()
        assert "flatpickr" in html
        assert 'name="event_date"' in html
        assert '"dateFormat":"Y-m-d"' in html

    def test_time_field_generates_no_calendar(self):
        class M(BaseModel):
            start_time: Annotated[str, TimeField()] = ""

        fi = M.model_fields["start_time"]
        comp = _field_to_component("start_time", fi)
        html = comp.render()
        assert '"noCalendar":true' in html

    def test_datetime_field_generates_enable_time(self):
        class M(BaseModel):
            starts_at: Annotated[str, DateTimeField()] = ""

        fi = M.model_fields["starts_at"]
        comp = _field_to_component("starts_at", fi)
        html = comp.render()
        assert '"enableTime":true' in html

    def test_date_field_with_value(self):
        class M(BaseModel):
            event_date: Annotated[str, DateField()] = ""

        fi = M.model_fields["event_date"]
        comp = _field_to_component("event_date", fi, value="2024-06-15")
        html = comp.render()
        assert 'value="2024-06-15"' in html

    def test_date_field_without_value(self):
        class M(BaseModel):
            event_date: Annotated[str, DateField()] = ""

        fi = M.model_fields["event_date"]
        comp = _field_to_component("event_date", fi)
        html = comp.render()
        assert 'value=""' in html


# --- TestAutoDetection ---


class TestAutoDetection:
    def test_datetime_date_type_auto_detected(self):
        class M(BaseModel):
            birthday: dt.date = dt.date(2000, 1, 1)

        fi = M.model_fields["birthday"]
        comp = _field_to_component("birthday", fi)
        html = comp.render()
        assert "flatpickr" in html
        assert '"dateFormat":"Y-m-d"' in html

    def test_datetime_time_type_auto_detected(self):
        class M(BaseModel):
            alarm: dt.time = dt.time(8, 0)

        fi = M.model_fields["alarm"]
        comp = _field_to_component("alarm", fi)
        html = comp.render()
        assert "flatpickr" in html
        assert '"noCalendar":true' in html

    def test_datetime_datetime_type_auto_detected(self):
        class M(BaseModel):
            created_at: dt.datetime = dt.datetime(2024, 1, 1, 12, 0)

        fi = M.model_fields["created_at"]
        comp = _field_to_component("created_at", fi)
        html = comp.render()
        assert "flatpickr" in html
        assert '"enableTime":true' in html

    def test_annotated_overrides_auto_detection(self):
        class M(BaseModel):
            birthday: Annotated[str, DateField(format="d/m/Y")] = ""

        fi = M.model_fields["birthday"]
        comp = _field_to_component("birthday", fi)
        html = comp.render()
        assert '"dateFormat":"d/m/Y"' in html


# --- TestPageIncludeFlatpickr ---


class TestPageIncludeFlatpickr:
    def test_include_flatpickr_adds_cdn(self):
        page = Page(title="Test", include_flatpickr=True)
        html = page.render()
        assert FLATPICKR_CSS_CDN in html
        assert FLATPICKR_JS_CDN in html

    def test_default_no_flatpickr(self):
        page = Page(title="Test")
        html = page.render()
        assert "flatpickr" not in html.lower()


# --- TestModelFormDatetime ---


class TestModelFormDatetime:
    def test_model_form_with_date_field(self):
        class Event(BaseModel):
            name: str = ""
            event_date: Annotated[str, DateField()] = ""

        form = ModelForm(Event, action="/create")
        html = form.render()
        assert "flatpickr" in html
        assert 'name="event_date"' in html

    def test_model_form_edit_mode(self):
        class Event(BaseModel):
            name: str = ""
            event_date: Annotated[str, DateField()] = ""

        instance = Event(name="Party", event_date="2024-06-15")
        form = ModelForm(Event, action="/edit", instance=instance)
        html = form.render()
        assert 'value="2024-06-15"' in html


# --- TestCRUDRouterDatetime ---


class TestCRUDRouterDatetime:
    def test_has_datetime_fields_with_annotation(self):
        from fastapi import FastAPI

        from kokage_ui.data.crud import CRUDRouter, InMemoryStorage

        class Event(BaseModel):
            id: str = ""
            name: str = ""
            event_date: Annotated[str, DateField()] = ""

        app = FastAPI()
        storage = InMemoryStorage(Event)
        router = CRUDRouter(app, "/events", Event, storage)
        assert router._has_datetime_fields() is True

    def test_has_datetime_fields_with_type(self):
        from fastapi import FastAPI

        from kokage_ui.data.crud import CRUDRouter, InMemoryStorage

        class Event(BaseModel):
            id: str = ""
            name: str = ""
            birthday: dt.date = dt.date(2000, 1, 1)

        app = FastAPI()
        storage = InMemoryStorage(Event)
        router = CRUDRouter(app, "/events", Event, storage)
        assert router._has_datetime_fields() is True

    def test_has_no_datetime_fields(self):
        from fastapi import FastAPI

        from kokage_ui.data.crud import CRUDRouter, InMemoryStorage

        class Item(BaseModel):
            id: str = ""
            name: str = ""

        app = FastAPI()
        storage = InMemoryStorage(Item)
        router = CRUDRouter(app, "/items", Item, storage)
        assert router._has_datetime_fields() is False

    def test_wrap_page_includes_flatpickr(self):
        from fastapi import FastAPI

        from kokage_ui.data.crud import CRUDRouter, InMemoryStorage
        from kokage_ui.elements import Div

        class Event(BaseModel):
            id: str = ""
            event_date: Annotated[str, DateField()] = ""

        app = FastAPI()
        storage = InMemoryStorage(Event)
        router = CRUDRouter(app, "/events", Event, storage)

        page = router._wrap_page(Div("test"), "Test")
        html = str(page)
        assert FLATPICKR_CSS_CDN in html
        assert FLATPICKR_JS_CDN in html
