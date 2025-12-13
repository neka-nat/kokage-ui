"""Tests for DaisyUI high-level components."""

from kokage_ui.components import (
    Alert,
    Badge,
    Card,
    DaisyButton,
    DaisyInput,
    DaisySelect,
    DaisyTable,
    DaisyTextarea,
    Hero,
    NavBar,
    Stat,
    Stats,
)


class TestCard:
    def test_basic_card(self):
        result = str(Card("Content"))
        assert "card" in result
        assert "card-body" in result
        assert "Content" in result

    def test_card_with_title(self):
        result = str(Card("Body", title="My Card"))
        assert "card-title" in result
        assert "My Card" in result

    def test_card_with_image(self):
        result = str(Card("Body", image="/photo.jpg", image_alt="Photo"))
        assert '<img src="/photo.jpg"' in result
        assert "<figure>" in result

    def test_card_compact(self):
        result = str(Card("Body", compact=True))
        assert "card-sm" in result

    def test_card_side(self):
        result = str(Card("Body", side=True))
        assert "lg:card-side" in result

    def test_card_with_actions(self):
        result = str(Card("Body", actions=[DaisyButton("OK", color="primary")]))
        assert "card-actions" in result
        assert "btn" in result


class TestStat:
    def test_basic_stat(self):
        result = str(Stat(title="Revenue", value="$12,345"))
        assert "stat-title" in result
        assert "Revenue" in result
        assert "stat-value" in result
        assert "$12,345" in result

    def test_stat_with_desc(self):
        result = str(Stat(title="Users", value="1,234", desc="+21%"))
        assert "stat-desc" in result
        assert "+21%" in result


class TestStats:
    def test_stats_container(self):
        result = str(
            Stats(
                Stat(title="A", value="1"),
                Stat(title="B", value="2"),
            )
        )
        assert "stats" in result
        assert "shadow" in result

    def test_stats_vertical(self):
        result = str(Stats(Stat(title="A", value="1"), vertical=True))
        assert "stats-vertical" in result


class TestHero:
    def test_basic_hero(self):
        result = str(Hero("Welcome"))
        assert "hero" in result
        assert "hero-content" in result
        assert "Welcome" in result

    def test_hero_min_height(self):
        result = str(Hero("Content", min_height="60vh"))
        assert "min-height: 60vh" in result

    def test_hero_overlay(self):
        result = str(Hero("Content", overlay=True))
        assert "hero-overlay" in result


class TestAlert:
    def test_basic_alert(self):
        result = str(Alert("Warning!"))
        assert "alert" in result
        assert "Warning!" in result

    def test_alert_variants(self):
        for variant in ("info", "success", "warning", "error"):
            result = str(Alert("msg", variant=variant))
            assert f"alert-{variant}" in result


class TestBadge:
    def test_basic_badge(self):
        result = str(Badge("New"))
        assert "badge" in result
        assert "New" in result

    def test_badge_color(self):
        result = str(Badge("Hot", color="error"))
        assert "badge-error" in result

    def test_badge_outline(self):
        result = str(Badge("Tag", outline=True))
        assert "badge-outline" in result

    def test_badge_size(self):
        result = str(Badge("S", size="sm"))
        assert "badge-sm" in result


class TestNavBar:
    def test_basic_navbar(self):
        result = str(NavBar(start="Logo", end="Menu"))
        assert "navbar" in result
        assert "navbar-start" in result
        assert "navbar-end" in result
        assert "Logo" in result
        assert "Menu" in result


class TestDaisyButton:
    def test_basic_button(self):
        result = str(DaisyButton("Click"))
        assert "btn" in result
        assert "Click" in result

    def test_button_color(self):
        result = str(DaisyButton("OK", color="primary"))
        assert "btn-primary" in result

    def test_button_variant(self):
        result = str(DaisyButton("Ghost", variant="ghost"))
        assert "btn-ghost" in result

    def test_button_size(self):
        result = str(DaisyButton("Big", size="lg"))
        assert "btn-lg" in result

    def test_button_disabled(self):
        result = str(DaisyButton("No", disabled=True))
        assert " disabled" in result


class TestDaisyInput:
    def test_basic_input(self):
        result = str(DaisyInput(name="email", placeholder="Email"))
        assert "input" in result
        assert 'name="email"' in result

    def test_input_with_label(self):
        result = str(DaisyInput(label="Email", name="email"))
        assert "label" in result
        assert "Email" in result


class TestDaisySelect:
    def test_basic_select(self):
        result = str(DaisySelect(options=["Red", "Blue"], name="color"))
        assert "select" in result
        assert 'value="Red"' in result
        assert 'value="Blue"' in result

    def test_select_tuples(self):
        result = str(DaisySelect(options=[("r", "Red"), ("b", "Blue")], name="color"))
        assert 'value="r"' in result
        assert "Red" in result


class TestDaisyTextarea:
    def test_basic_textarea(self):
        result = str(DaisyTextarea(name="bio", placeholder="Bio"))
        assert "textarea" in result
        assert 'name="bio"' in result


class TestDaisyTable:
    def test_basic_table(self):
        result = str(
            DaisyTable(
                headers=["Name", "Age"],
                rows=[["Alice", "30"], ["Bob", "25"]],
            )
        )
        assert "<th>Name</th>" in result
        assert "<td>Alice</td>" in result

    def test_table_zebra(self):
        result = str(
            DaisyTable(
                headers=["A"],
                rows=[["1"]],
                zebra=True,
            )
        )
        assert "table-zebra" in result

    def test_table_compact(self):
        result = str(
            DaisyTable(
                headers=["A"],
                rows=[["1"]],
                compact=True,
            )
        )
        assert "table-xs" in result
