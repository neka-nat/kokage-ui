"""Tests for Autocomplete / Combobox component."""

from kokage_ui.components import Autocomplete, autocomplete_option


class TestAutocomplete:
    def test_basic_render(self):
        result = str(Autocomplete(name="user_id", search_url="/search"))
        assert "form-control" in result
        assert 'name="user_id"' in result
        assert 'hx-get="/search"' in result

    def test_label(self):
        result = str(Autocomplete(name="x", search_url="/s", label="User"))
        assert "label-text" in result
        assert "User" in result

    def test_no_label(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert "label-text" not in result

    def test_hidden_input(self):
        result = str(Autocomplete(name="user_id", search_url="/s"))
        assert 'type="hidden"' in result
        assert 'name="user_id"' in result

    def test_display_input(self):
        result = str(Autocomplete(name="user_id", search_url="/s"))
        assert 'name="user_id_display"' in result
        assert 'type="text"' in result

    def test_custom_display_name(self):
        result = str(
            Autocomplete(name="uid", search_url="/s", display_name="user_search")
        )
        assert 'name="user_search"' in result

    def test_initial_value(self):
        result = str(Autocomplete(name="x", search_url="/s", value="42"))
        assert 'value="42"' in result

    def test_initial_display_value(self):
        result = str(
            Autocomplete(name="x", search_url="/s", display_value="Alice")
        )
        assert 'value="Alice"' in result

    def test_placeholder(self):
        result = str(
            Autocomplete(name="x", search_url="/s", placeholder="Search...")
        )
        assert 'placeholder="Search..."' in result

    def test_delay(self):
        result = str(Autocomplete(name="x", search_url="/s", delay=500))
        assert "delay:500ms" in result

    def test_default_delay(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert "delay:300ms" in result

    def test_min_chars_default(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        # >= is HTML-escaped to &gt;= in attribute values
        assert "[this.value.length &gt;= 1]" in result

    def test_min_chars_custom(self):
        result = str(Autocomplete(name="x", search_url="/s", min_chars=3))
        assert "[this.value.length &gt;= 3]" in result

    def test_min_chars_zero(self):
        result = str(Autocomplete(name="x", search_url="/s", min_chars=0))
        assert "[this.value.length" not in result

    def test_bordered(self):
        result = str(Autocomplete(name="x", search_url="/s", bordered=True))
        assert "input-bordered" in result

    def test_not_bordered(self):
        result = str(Autocomplete(name="x", search_url="/s", bordered=False))
        assert "input-bordered" not in result

    def test_aria_attributes(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert 'role="combobox"' in result
        assert 'aria-autocomplete="list"' in result
        assert 'aria-expanded="false"' in result

    def test_listbox_role(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert 'role="listbox"' in result

    def test_listbox_classes(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert "dropdown-content" in result
        assert "bg-base-200" in result

    def test_script_present(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert "<script>" in result
        assert "MutationObserver" in result

    def test_custom_id(self):
        result = str(
            Autocomplete(name="x", search_url="/s", autocomplete_id="my-ac")
        )
        assert 'id="my-ac"' in result
        assert 'id="my-ac-listbox"' in result

    def test_form_control_wrapper(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert "form-control w-full" in result

    def test_xss_escape_label(self):
        result = str(
            Autocomplete(name="x", search_url="/s", label='<script>alert("xss")</script>')
        )
        assert "<script>alert" not in result
        assert "&lt;script&gt;" in result

    def test_xss_escape_placeholder(self):
        result = str(
            Autocomplete(name="x", search_url="/s", placeholder='"><script>')
        )
        assert '"><script>' not in result

    def test_hx_target_matches_listbox_id(self):
        result = str(
            Autocomplete(name="x", search_url="/s", autocomplete_id="test-ac")
        )
        assert 'hx-target="#test-ac-listbox"' in result
        assert 'id="test-ac-listbox"' in result

    def test_aria_controls_matches_listbox_id(self):
        result = str(
            Autocomplete(name="x", search_url="/s", autocomplete_id="test-ac")
        )
        assert 'aria-controls="test-ac-listbox"' in result

    def test_autocomplete_off(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert 'autocomplete="off"' in result

    def test_dropdown_wrapper(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert "dropdown dropdown-open" in result

    def test_listbox_hidden_by_default(self):
        result = str(Autocomplete(name="x", search_url="/s"))
        assert 'style="display:none"' in result


class TestAutocompleteOption:
    def test_basic_option(self):
        result = str(autocomplete_option("42", "Alice Smith"))
        assert 'data-value="42"' in result
        assert 'role="option"' in result
        assert "Alice Smith" in result
        assert "<li" in result
        assert "<a>" in result

    def test_xss_escape_label(self):
        result = str(autocomplete_option("1", "<script>alert(1)</script>"))
        assert "<script>alert" not in result
        assert "&lt;script&gt;" in result

    def test_xss_escape_value(self):
        result = str(autocomplete_option('"><img src=x>', "Test"))
        assert '"><img' not in result

    def test_extra_attrs(self):
        result = str(autocomplete_option("1", "Alice", cls="extra"))
        assert 'class="extra"' in result
