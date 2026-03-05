"""Tests for theme switching components."""

from kokage_ui.theme import ALL_THEMES, DarkModeToggle, ThemeSwitcher


class TestDarkModeToggle:
    def test_renders_swap_checkbox(self):
        html = DarkModeToggle().render()
        assert "swap swap-rotate" in html
        assert 'type="checkbox"' in html
        assert "kokage-dm-" in html

    def test_sun_moon_svgs(self):
        html = DarkModeToggle().render()
        assert "swap-off" in html
        assert "swap-on" in html
        assert "<svg" in html

    def test_inline_script(self):
        html = DarkModeToggle().render()
        assert "<script>" in html
        assert "localStorage" in html
        assert "data-theme" in html

    def test_custom_themes(self):
        html = DarkModeToggle(light_theme="corporate", dark_theme="business").render()
        assert "LIGHT='corporate'" in html
        assert "DARK='business'" in html

    def test_custom_key(self):
        html = DarkModeToggle(key="my-theme").render()
        assert "KEY='my-theme'" in html

    def test_size_parameter(self):
        html = DarkModeToggle(size="h-5 w-5").render()
        assert "h-5 w-5" in html

    def test_default_size(self):
        html = DarkModeToggle().render()
        assert "h-6 w-6" in html

    def test_unique_ids(self):
        html1 = DarkModeToggle().render()
        html2 = DarkModeToggle().render()
        # Extract checkbox IDs - they should differ
        import re

        ids1 = re.findall(r"kokage-dm-[a-f0-9]+", html1)
        ids2 = re.findall(r"kokage-dm-[a-f0-9]+", html2)
        assert ids1[0] != ids2[0]


class TestThemeSwitcher:
    def test_renders_dropdown(self):
        html = ThemeSwitcher().render()
        assert "dropdown dropdown-end" in html
        assert "dropdown-content" in html

    def test_default_themes(self):
        html = ThemeSwitcher().render()
        for theme in ["light", "dark", "cupcake", "dracula", "nord"]:
            assert f'data-theme="{theme}"' in html

    def test_all_default_themes_present(self):
        html = ThemeSwitcher().render()
        for theme in ALL_THEMES:
            assert theme in html

    def test_custom_themes(self):
        html = ThemeSwitcher(themes=["corporate", "business", "nord"]).render()
        assert 'data-theme="corporate"' in html
        assert 'data-theme="business"' in html
        assert 'data-theme="nord"' in html
        # Should not include themes not in the list
        assert 'data-theme="dracula"' not in html

    def test_color_preview_spans(self):
        html = ThemeSwitcher().render()
        assert "bg-primary" in html
        assert "bg-secondary" in html
        assert "bg-accent" in html
        assert "bg-neutral" in html

    def test_trigger_label(self):
        html = ThemeSwitcher(label="Style").render()
        assert "Style" in html

    def test_trigger_size(self):
        html = ThemeSwitcher(size="lg").render()
        assert "btn-lg" in html

    def test_script_with_kokage_set_theme(self):
        html = ThemeSwitcher().render()
        assert "kokageSetTheme" in html
        assert "localStorage" in html

    def test_custom_key(self):
        html = ThemeSwitcher(key="app-theme").render()
        assert "KEY='app-theme'" in html

    def test_extra_cls(self):
        html = ThemeSwitcher(cls="ml-2").render()
        assert "dropdown dropdown-end ml-2" in html
