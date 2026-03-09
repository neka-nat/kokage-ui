"""Tests for DaisyUI high-level components."""

from kokage_ui.components import (
    Accordion,
    Alert,
    Badge,
    Breadcrumb,
    Card,
    Collapse,
    DaisyButton,
    DaisyInput,
    DaisySelect,
    DaisyTable,
    DaisyTextarea,
    Drawer,
    Dropdown,
    Hero,
    Layout,
    Modal,
    NavBar,
    Stat,
    Stats,
    Step,
    Steps,
    Tab,
    Tabs,
    Toast,
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


class TestToast:
    def test_basic_toast(self):
        result = str(Toast("Hello"))
        assert "toast" in result
        assert "z-50" in result
        assert "Hello" in result

    def test_toast_variant(self):
        result = str(Toast("Error!", variant="error"))
        assert "alert-error" in result

    def test_toast_position(self):
        result = str(Toast("Msg", position="toast-start toast-bottom"))
        assert "toast-start" in result
        assert "toast-bottom" in result

    def test_toast_default_position(self):
        result = str(Toast("Msg"))
        assert "toast-end" in result
        assert "toast-top" in result


class TestLayout:
    def test_wrap_basic(self):
        layout = Layout()
        page = layout.wrap("Content", "Title")
        html = page.render()
        assert "Content" in html
        assert "<title>Title</title>" in html

    def test_wrap_with_navbar(self):
        layout = Layout(navbar=NavBar(start="Logo"))
        page = layout.wrap("Body", "Test")
        html = page.render()
        assert "navbar" in html
        assert "Logo" in html
        assert "Body" in html

    def test_wrap_with_sidebar(self):
        from kokage_ui.elements import Div

        sidebar = Div("Sidebar", cls="w-64")
        layout = Layout(sidebar=sidebar)
        page = layout.wrap("Main", "Test")
        html = page.render()
        assert "Sidebar" in html
        assert "flex" in html

    def test_wrap_with_footer(self):
        from kokage_ui.elements import Footer

        layout = Layout(footer=Footer("Footer text"))
        page = layout.wrap("Body", "Test")
        html = page.render()
        assert "Footer text" in html

    def test_wrap_title_suffix(self):
        layout = Layout(title_suffix=" - My App")
        page = layout.wrap("Content", "Home")
        html = page.render()
        assert "<title>Home - My App</title>" in html

    def test_wrap_include_toast(self):
        layout = Layout(include_toast=True)
        page = layout.wrap("Content", "Test")
        html = page.render()
        assert "kokage-toast" in html

    def test_wrap_theme(self):
        layout = Layout(theme="dark")
        page = layout.wrap("Content", "Test")
        html = page.render()
        assert 'data-theme="dark"' in html


class TestModal:
    def test_basic_modal(self):
        result = str(Modal("Content", modal_id="my-modal"))
        assert "<dialog" in result
        assert 'id="my-modal"' in result
        assert "modal" in result
        assert "modal-box" in result
        assert "Content" in result

    def test_modal_with_title(self):
        result = str(Modal("Body", modal_id="m1", title="Title"))
        assert "Title" in result
        assert "<h3" in result

    def test_modal_with_actions(self):
        result = str(
            Modal("Body", modal_id="m1", actions=[DaisyButton("OK")])
        )
        assert "modal-action" in result
        assert "OK" in result

    def test_modal_closable(self):
        result = str(Modal("Body", modal_id="m1", closable=True))
        assert "modal-backdrop" in result
        assert 'method="dialog"' in result

    def test_modal_not_closable(self):
        result = str(Modal("Body", modal_id="m1", closable=False))
        assert "modal-backdrop" not in result


class TestDrawer:
    def test_basic_drawer(self):
        result = str(Drawer(content="Main", side="Side"))
        assert "drawer" in result
        assert "drawer-content" in result
        assert "drawer-side" in result
        assert "drawer-toggle" in result
        assert "Main" in result
        assert "Side" in result

    def test_drawer_end(self):
        result = str(Drawer(content="Main", side="Side", end=True))
        assert "drawer-end" in result

    def test_drawer_open(self):
        result = str(Drawer(content="Main", side="Side", open=True))
        assert "checked" in result

    def test_drawer_custom_id(self):
        result = str(Drawer(content="M", side="S", drawer_id="my-drawer"))
        assert 'id="my-drawer"' in result


class TestTabs:
    def test_link_tabs(self):
        result = str(Tabs(tabs=[
            Tab(label="Tab 1", href="/t1"),
            Tab(label="Tab 2", href="/t2"),
        ]))
        assert "tabs" in result
        assert "Tab 1" in result
        assert 'href="/t1"' in result

    def test_active_tab(self):
        result = str(Tabs(tabs=[
            Tab(label="A", href="/a", active=True),
            Tab(label="B", href="/b"),
        ]))
        assert "tab-active" in result

    def test_disabled_tab(self):
        result = str(Tabs(tabs=[
            Tab(label="A", href="/a"),
            Tab(label="B", href="/b", disabled=True),
        ]))
        assert "tab-disabled" in result

    def test_content_tabs(self):
        result = str(Tabs(tabs=[
            Tab(label="Tab 1", content="Content 1", active=True),
            Tab(label="Tab 2", content="Content 2"),
        ]))
        assert 'type="radio"' in result
        assert "tab-content" in result
        assert "Content 1" in result

    def test_tabs_variant(self):
        result = str(Tabs(tabs=[Tab(label="A", href="/a")], variant="bordered"))
        assert "tabs-bordered" in result

    def test_tabs_size(self):
        result = str(Tabs(tabs=[Tab(label="A", href="/a")], size="lg"))
        assert "tabs-lg" in result

    def test_tabs_boxed(self):
        result = str(Tabs(tabs=[Tab(label="A", href="/a")], variant="boxed"))
        assert "tabs-boxed" in result


class TestSteps:
    def test_basic_steps(self):
        result = str(Steps(steps=[
            Step(label="Register"),
            Step(label="Choose"),
            Step(label="Pay"),
        ], current=1))
        assert "steps" in result
        assert "Register" in result
        assert "step-primary" in result

    def test_steps_current(self):
        result = str(Steps(steps=[
            Step(label="A"),
            Step(label="B"),
            Step(label="C"),
        ], current=0))
        # Only first step should have color
        assert result.count("step-primary") == 1

    def test_steps_vertical(self):
        result = str(Steps(steps=[Step(label="A")], vertical=True))
        assert "steps-vertical" in result

    def test_steps_color(self):
        result = str(Steps(steps=[Step(label="A")], current=0, color="accent"))
        assert "step-accent" in result

    def test_step_data_content(self):
        result = str(Steps(steps=[Step(label="A", data_content="★")], current=0))
        assert "data-content" in result

    def test_step_per_step_color(self):
        result = str(Steps(steps=[
            Step(label="A", color="error"),
            Step(label="B"),
        ], current=1))
        assert "step-error" in result
        assert "step-primary" in result


class TestBreadcrumb:
    def test_basic_breadcrumb(self):
        result = str(Breadcrumb(items=[
            ("Home", "/"),
            ("Users", "/users"),
            ("Alice", None),
        ]))
        assert "breadcrumbs" in result
        assert 'href="/"' in result
        assert "Alice" in result

    def test_breadcrumb_no_link(self):
        result = str(Breadcrumb(items=[("Current", None)]))
        assert "<span>" in result
        assert "<a" not in result or 'href' not in result.split("Current")[0].split("<")[-1]

    def test_breadcrumb_all_links(self):
        result = str(Breadcrumb(items=[
            ("A", "/a"),
            ("B", "/b"),
        ]))
        assert result.count("href=") == 2


class TestCollapse:
    def test_basic_collapse(self):
        result = str(Collapse("Title", "Content"))
        assert "collapse" in result
        assert "collapse-title" in result
        assert "collapse-content" in result
        assert "Title" in result
        assert "Content" in result

    def test_collapse_open(self):
        result = str(Collapse("T", "C", open=True))
        assert "checked" in result

    def test_collapse_variant_arrow(self):
        result = str(Collapse("T", "C", variant="arrow"))
        assert "collapse-arrow" in result

    def test_collapse_variant_plus(self):
        result = str(Collapse("T", "C", variant="plus"))
        assert "collapse-plus" in result

    def test_collapse_with_name(self):
        result = str(Collapse("T", "C", name="acc"))
        assert 'type="radio"' in result
        assert 'name="acc"' in result

    def test_collapse_without_name(self):
        result = str(Collapse("T", "C"))
        assert 'type="checkbox"' in result


class TestAccordion:
    def test_basic_accordion(self):
        result = str(Accordion(items=[
            ("Section 1", "Content 1"),
            ("Section 2", "Content 2"),
        ]))
        assert "collapse" in result
        assert "Section 1" in result
        assert "Content 2" in result
        assert 'name="accordion"' in result

    def test_accordion_default_open(self):
        result = str(Accordion(items=[
            ("A", "C1"),
            ("B", "C2"),
        ], default_open=0))
        assert "checked" in result

    def test_accordion_variant(self):
        result = str(Accordion(items=[("A", "C")], variant="arrow"))
        assert "collapse-arrow" in result

    def test_accordion_custom_name(self):
        result = str(Accordion(items=[("A", "C")], name="faq"))
        assert 'name="faq"' in result


class TestDropdown:
    def test_basic_dropdown_with_items(self):
        result = str(Dropdown(
            "Options",
            items=[("Edit", "/edit"), ("Delete", "/delete")],
        ))
        assert "dropdown" in result
        assert "Options" in result
        assert "Edit" in result
        assert 'href="/edit"' in result

    def test_dropdown_string_trigger(self):
        result = str(Dropdown("Menu", items=[("A", "/a")]))
        assert 'role="button"' in result
        assert "btn" in result

    def test_dropdown_component_trigger(self):
        btn = DaisyButton("Menu", color="ghost")
        result = str(Dropdown(btn, items=[("A", "/a")]))
        assert "btn-ghost" in result

    def test_dropdown_position(self):
        result = str(Dropdown("M", items=[("A", "/a")], position="top"))
        assert "dropdown-top" in result

    def test_dropdown_hover(self):
        result = str(Dropdown("M", items=[("A", "/a")], hover=True))
        assert "dropdown-hover" in result

    def test_dropdown_align_end(self):
        result = str(Dropdown("M", items=[("A", "/a")], align_end=True))
        assert "dropdown-end" in result

    def test_dropdown_custom_children(self):
        from kokage_ui.elements import Ul, Li, A

        result = str(Dropdown("Trigger", Ul(Li(A("Custom")))))
        assert "Custom" in result
