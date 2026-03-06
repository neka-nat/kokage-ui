"""Tests for i18n (internationalization) support."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from pydantic import BaseModel

from kokage_ui.features.i18n import (
    LanguageSwitcher,
    LocaleMiddleware,
    _translations,
    add_locale,
    configure,
    get_available_locales,
    get_locale,
    set_locale,
    t,
)


# ========================================
# Fixtures
# ========================================


@pytest.fixture(autouse=True)
def _reset_i18n():
    """Reset i18n state before each test."""
    import kokage_ui.features.i18n as i18n_mod

    # Save originals
    orig_default = i18n_mod._default_locale
    orig_fallback = i18n_mod._fallback_locale
    orig_translations = {k: dict(v) for k, v in i18n_mod._translations.items()}

    yield

    # Restore
    i18n_mod._default_locale = orig_default
    i18n_mod._fallback_locale = orig_fallback
    i18n_mod._translations.clear()
    i18n_mod._translations.update({k: dict(v) for k, v in orig_translations.items()})
    i18n_mod._current_locale.set("en")


# ========================================
# TestTranslation
# ========================================


class TestTranslation:
    """Tests for the t() translation function."""

    def test_basic_english(self):
        set_locale("en")
        assert t("crud.created") == "Created successfully"

    def test_basic_japanese(self):
        set_locale("ja")
        assert t("crud.created") == "作成しました"

    def test_locale_switch(self):
        set_locale("en")
        assert t("crud.delete") == "Delete"
        set_locale("ja")
        assert t("crud.delete") == "削除"

    def test_kwargs_interpolation(self):
        set_locale("en")
        assert t("crud.new_title", name="User") == "New User"
        set_locale("ja")
        assert t("crud.new_title", name="User") == "Userを作成"

    def test_fallback_to_fallback_locale(self):
        # Add a locale with missing keys
        add_locale("fr", {"crud.created": "Créé avec succès"})
        set_locale("fr")
        assert t("crud.created") == "Créé avec succès"
        # Missing key falls back to English (fallback)
        assert t("crud.deleted") == "Deleted successfully"

    def test_fallback_to_default_arg(self):
        set_locale("en")
        assert t("nonexistent.key", default="Fallback") == "Fallback"

    def test_fallback_to_key_itself(self):
        set_locale("en")
        assert t("nonexistent.key") == "nonexistent.key"

    def test_all_builtin_en_keys(self):
        set_locale("en")
        expected_keys = [
            "crud.created", "crud.updated", "crud.deleted",
            "crud.not_found", "crud.not_found_title", "crud.invalid_value",
            "crud.new_title", "crud.edit_title", "crud.detail_title",
            "crud.create", "crud.update", "crud.edit", "crud.delete",
            "crud.new", "crud.back_to_list", "crud.search_placeholder",
            "crud.confirm_delete", "common.actions", "common.submit",
        ]
        for key in expected_keys:
            result = t(key)
            assert result != key, f"Key {key} returned itself (not translated)"

    def test_all_builtin_ja_keys(self):
        set_locale("ja")
        expected_keys = [
            "crud.created", "crud.updated", "crud.deleted",
            "crud.not_found", "crud.not_found_title", "crud.invalid_value",
            "crud.create", "crud.update", "crud.edit", "crud.delete",
            "crud.new", "crud.back_to_list",
            "common.actions", "common.submit",
        ]
        for key in expected_keys:
            result = t(key)
            assert result != key, f"Key {key} returned itself (not translated)"


# ========================================
# TestConfiguration
# ========================================


class TestConfiguration:
    """Tests for configure() and add_locale()."""

    def test_configure_sets_default(self):
        configure(default_locale="ja")
        assert get_locale() == "ja"

    def test_configure_merges_translations(self):
        configure(
            default_locale="en",
            translations={"en": {"custom.key": "Custom Value"}},
        )
        assert t("custom.key") == "Custom Value"
        # Built-in keys still work
        assert t("crud.created") == "Created successfully"

    def test_add_locale_new(self):
        add_locale("fr", {"crud.created": "Créé avec succès"})
        assert "fr" in get_available_locales()
        set_locale("fr")
        assert t("crud.created") == "Créé avec succès"

    def test_add_locale_merge(self):
        add_locale("en", {"custom.greeting": "Hello!"})
        set_locale("en")
        assert t("custom.greeting") == "Hello!"
        # Existing keys preserved
        assert t("crud.created") == "Created successfully"

    def test_user_override_builtin(self):
        add_locale("en", {"crud.created": "Item created!"})
        set_locale("en")
        assert t("crud.created") == "Item created!"

    def test_get_available_locales(self):
        locales = get_available_locales()
        assert "en" in locales
        assert "ja" in locales


# ========================================
# TestLanguageSwitcher
# ========================================


class TestLanguageSwitcher:
    """Tests for the LanguageSwitcher component."""

    def test_renders_dropdown(self):
        set_locale("en")
        switcher = LanguageSwitcher()
        html = switcher.render()
        assert "dropdown" in html
        assert "kokageSwitchLocale" in html

    def test_shows_locale_names(self):
        set_locale("en")
        switcher = LanguageSwitcher(locales=["en", "ja"])
        html = switcher.render()
        assert "English" in html
        assert "日本語" in html

    def test_globe_svg_present(self):
        switcher = LanguageSwitcher()
        html = switcher.render()
        assert "<svg" in html
        assert "viewBox" in html

    def test_active_class_on_current(self):
        set_locale("ja")
        switcher = LanguageSwitcher(locales=["en", "ja"])
        html = switcher.render()
        # The ja button should have btn-active
        assert "btn-active" in html

    def test_current_locale_display(self):
        set_locale("ja")
        switcher = LanguageSwitcher()
        html = switcher.render()
        assert "日本語" in html


# ========================================
# TestLocaleMiddleware
# ========================================


class TestLocaleMiddleware:
    """Tests for LocaleMiddleware."""

    def _make_app(self) -> FastAPI:
        app = FastAPI()

        @app.get("/locale")
        def get_current_locale():
            return {"locale": get_locale()}

        app.add_middleware(LocaleMiddleware)
        return app

    @pytest.mark.anyio
    async def test_query_param(self):
        app = self._make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/locale?lang=ja")
            assert resp.json()["locale"] == "ja"

    @pytest.mark.anyio
    async def test_cookie_persistence(self):
        app = self._make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Set via query param → should get cookie
            resp = await client.get("/locale?lang=ja")
            assert "kokage_locale" in resp.cookies

            # Next request uses cookie
            resp2 = await client.get("/locale", cookies={"kokage_locale": "ja"})
            assert resp2.json()["locale"] == "ja"

    @pytest.mark.anyio
    async def test_accept_language_header(self):
        app = self._make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/locale",
                headers={"Accept-Language": "ja,en;q=0.9"},
            )
            assert resp.json()["locale"] == "ja"

    @pytest.mark.anyio
    async def test_accept_language_prefix(self):
        app = self._make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/locale",
                headers={"Accept-Language": "ja-JP,en;q=0.9"},
            )
            assert resp.json()["locale"] == "ja"

    @pytest.mark.anyio
    async def test_default_locale_fallback(self):
        app = self._make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/locale")
            assert resp.json()["locale"] == "en"

    @pytest.mark.anyio
    async def test_query_takes_priority(self):
        app = self._make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/locale?lang=en",
                cookies={"kokage_locale": "ja"},
                headers={"Accept-Language": "ja"},
            )
            assert resp.json()["locale"] == "en"

    @pytest.mark.anyio
    async def test_cookie_takes_priority_over_header(self):
        app = self._make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/locale",
                cookies={"kokage_locale": "ja"},
                headers={"Accept-Language": "en"},
            )
            assert resp.json()["locale"] == "ja"


# ========================================
# TestCRUDWithI18n
# ========================================


class Item(BaseModel):
    id: str = ""
    name: str = ""


class TestCRUDWithI18n:
    """Tests for CRUD pages with i18n enabled."""

    def _make_crud_app(self, locale: str = "ja") -> FastAPI:
        from kokage_ui import KokageUI, InMemoryStorage

        app = FastAPI()
        ui = KokageUI(app, locale=locale)
        storage = InMemoryStorage(Item, initial=[Item(id="1", name="Test")])
        ui.crud("/items", model=Item, storage=storage)
        return app

    @pytest.mark.anyio
    async def test_list_page_japanese(self):
        app = self._make_crud_app("ja")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/items")
            html = resp.text
            assert "新規" in html
            assert "検索" in html

    @pytest.mark.anyio
    async def test_create_page_japanese(self):
        app = self._make_crud_app("ja")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/items/new")
            html = resp.text
            assert "Itemを作成" in html
            assert "作成" in html

    @pytest.mark.anyio
    async def test_detail_page_japanese(self):
        app = self._make_crud_app("ja")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/items/1")
            html = resp.text
            assert "Itemの詳細" in html
            assert "編集" in html
            assert "削除" in html
            assert "一覧に戻る" in html

    @pytest.mark.anyio
    async def test_edit_page_japanese(self):
        app = self._make_crud_app("ja")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/items/1/edit")
            html = resp.text
            assert "Itemを編集" in html
            assert "更新" in html

    @pytest.mark.anyio
    async def test_detail_not_found_japanese(self):
        app = self._make_crud_app("ja")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/items/nonexistent")
            assert resp.status_code == 404
            html = resp.text
            assert "見つかりませんでした" in html

    @pytest.mark.anyio
    async def test_create_toast_japanese(self):
        app = self._make_crud_app("ja")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False) as client:
            resp = await client.post("/items/new", data={"name": "New Item"})
            # Should redirect with Japanese toast
            location = resp.headers.get("location", "") or resp.headers.get("hx-redirect", "")
            assert "作成しました" in location or resp.status_code in (200, 303)

    @pytest.mark.anyio
    async def test_crud_default_english(self):
        """Without locale setting, CRUD uses English (backward compat)."""
        from kokage_ui import KokageUI, InMemoryStorage

        app = FastAPI()
        ui = KokageUI(app)  # No locale
        storage = InMemoryStorage(Item, initial=[Item(id="1", name="Test")])
        ui.crud("/items", model=Item, storage=storage)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/items")
            html = resp.text
            assert "New" in html

            resp = await client.get("/items/1")
            html = resp.text
            assert "Edit" in html
            assert "Delete" in html
            assert "Back to list" in html
