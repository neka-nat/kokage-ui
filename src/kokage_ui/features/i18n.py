"""Internationalization (i18n) support for kokage-ui.

Provides a contextvars-based translation system with locale middleware
and a language switcher component.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from kokage_ui.elements import Component, Div, Raw, Script, Span

# ========================================
# State
# ========================================

_current_locale: ContextVar[str] = ContextVar("_current_locale", default="en")
_default_locale: str = "en"
_fallback_locale: str = "en"

# ========================================
# Built-in translations
# ========================================

_BUILTIN_EN: dict[str, str] = {
    "crud.created": "Created successfully",
    "crud.updated": "Updated successfully",
    "crud.deleted": "Deleted successfully",
    "crud.not_found": "Not found.",
    "crud.not_found_title": "Not Found",
    "crud.invalid_value": "Invalid value",
    "crud.new_title": "New {name}",
    "crud.edit_title": "Edit {name}",
    "crud.detail_title": "{name} Detail",
    "crud.create": "Create",
    "crud.update": "Update",
    "crud.edit": "Edit",
    "crud.delete": "Delete",
    "crud.new": "New",
    "crud.back_to_list": "Back to list",
    "crud.search_placeholder": "Search {title}...",
    "crud.confirm_delete": "Delete this {name}?",
    "common.actions": "Actions",
    "common.submit": "Submit",
}

_BUILTIN_JA: dict[str, str] = {
    "crud.created": "作成しました",
    "crud.updated": "更新しました",
    "crud.deleted": "削除しました",
    "crud.not_found": "見つかりませんでした。",
    "crud.not_found_title": "見つかりません",
    "crud.invalid_value": "無効な値です",
    "crud.new_title": "{name}を作成",
    "crud.edit_title": "{name}を編集",
    "crud.detail_title": "{name}の詳細",
    "crud.create": "作成",
    "crud.update": "更新",
    "crud.edit": "編集",
    "crud.delete": "削除",
    "crud.new": "新規",
    "crud.back_to_list": "一覧に戻る",
    "crud.search_placeholder": "{title}を検索...",
    "crud.confirm_delete": "この{name}を削除しますか？",
    "common.actions": "操作",
    "common.submit": "送信",
}

_translations: dict[str, dict[str, str]] = {
    "en": dict(_BUILTIN_EN),
    "ja": dict(_BUILTIN_JA),
}

# ========================================
# Configuration
# ========================================


def configure(
    default_locale: str = "en",
    fallback_locale: str = "en",
    translations: dict[str, dict[str, str]] | None = None,
) -> None:
    """Configure i18n settings.

    Args:
        default_locale: Default locale code.
        fallback_locale: Fallback locale when key is missing.
        translations: Additional translations to merge (locale -> {key: value}).
    """
    global _default_locale, _fallback_locale
    _default_locale = default_locale
    _fallback_locale = fallback_locale
    _current_locale.set(default_locale)

    if translations:
        for locale, messages in translations.items():
            add_locale(locale, messages)


def add_locale(locale: str, messages: dict[str, str]) -> None:
    """Add or merge translations for a locale.

    Args:
        locale: Locale code (e.g. "en", "ja", "fr").
        messages: Translation key-value pairs.
    """
    if locale in _translations:
        _translations[locale].update(messages)
    else:
        _translations[locale] = dict(messages)


def get_locale() -> str:
    """Get the current locale for this request context."""
    return _current_locale.get()


def set_locale(locale: str) -> None:
    """Set the current locale for this request context."""
    _current_locale.set(locale)


def get_available_locales() -> list[str]:
    """Return list of available locale codes."""
    return list(_translations.keys())


# ========================================
# Translation function
# ========================================


def t(key: str, default: str | None = None, **kwargs: Any) -> str:
    """Translate a key to the current locale.

    Lookup order: current locale → fallback locale → default arg → key itself.
    Use kwargs for string interpolation: ``t("crud.new_title", name="User")``.

    Args:
        key: Translation key (e.g. "crud.created").
        default: Fallback string if key is not found in any locale.
        **kwargs: Variables for str.format() interpolation.

    Returns:
        Translated string.
    """
    locale = _current_locale.get()
    result = _translations.get(locale, {}).get(key)
    if result is None:
        result = _translations.get(_fallback_locale, {}).get(key)
    if result is None:
        result = default if default is not None else key
    if kwargs:
        result = result.format(**kwargs)
    return result


# ========================================
# Locale Middleware
# ========================================


def _parse_accept_language(header: str) -> str | None:
    """Extract the best matching locale from Accept-Language header."""
    available = set(_translations.keys())
    # Parse "en-US,en;q=0.9,ja;q=0.8" → sorted by quality
    parts: list[tuple[float, str]] = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue
        if ";q=" in part:
            lang, q = part.split(";q=", 1)
            try:
                quality = float(q)
            except ValueError:
                quality = 0.0
        else:
            lang = part
            quality = 1.0
        parts.append((quality, lang.strip()))

    parts.sort(key=lambda x: x[0], reverse=True)
    for _, lang in parts:
        # Try exact match first, then language prefix
        if lang in available:
            return lang
        prefix = lang.split("-")[0]
        if prefix in available:
            return prefix
    return None


class LocaleMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that detects and sets the request locale.

    Detection order:
    1. ``?lang=`` query parameter (also sets cookie for persistence)
    2. ``kokage_locale`` cookie
    3. ``Accept-Language`` header
    4. Default locale
    """

    COOKIE_NAME = "kokage_locale"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        available = set(_translations.keys())

        # 1. Query parameter
        lang = request.query_params.get("lang")
        set_cookie = False
        if lang and lang in available:
            set_cookie = True
        else:
            # 2. Cookie
            lang = request.cookies.get(self.COOKIE_NAME)
            if lang and lang not in available:
                lang = None
            if not lang:
                # 3. Accept-Language header
                accept = request.headers.get("accept-language", "")
                if accept:
                    lang = _parse_accept_language(accept)

        locale = lang or _default_locale
        _current_locale.set(locale)

        response = await call_next(request)

        if set_cookie:
            response.set_cookie(
                self.COOKIE_NAME,
                locale,
                max_age=365 * 24 * 60 * 60,
                httponly=False,
                samesite="lax",
            )

        return response


# ========================================
# LanguageSwitcher Component
# ========================================

_LOCALE_DISPLAY_NAMES: dict[str, str] = {
    "en": "English",
    "ja": "日本語",
    "zh": "中文",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português",
    "it": "Italiano",
    "ru": "Русский",
}

_GLOBE_SVG = (
    '<svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none"'
    ' viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">'
    '<path stroke-linecap="round" stroke-linejoin="round"'
    ' d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0'
    " 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997"
    " 0 017.843 6.082M12 3a8.997 8.997 0 00-7.843 6.082m15.686 0A11.953 11.953 0 0112"
    ' 10.5c-2.998 0-5.74 1.1-7.843 2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099'
    ' 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5a17.92 17.92 0 01-8.716-2.247m0'
    ' 0A8.966 8.966 0 003 12c0-1.97.633-3.794 1.716-5.277"/>'
    "</svg>"
)


class LanguageSwitcher(Component):
    """DaisyUI dropdown for switching the UI locale.

    Clicking a locale appends ``?lang=xx`` to the current URL and reloads.

    Args:
        locales: List of locale codes to show. Defaults to all available locales.
        size: Button size (xs, sm, md, lg).
    """

    tag = "div"

    def __init__(
        self,
        *,
        locales: list[str] | None = None,
        size: str = "sm",
        **attrs: Any,
    ) -> None:
        locale_list = locales if locales is not None else get_available_locales()
        current = get_locale()

        current_display = _LOCALE_DISPLAY_NAMES.get(current, current)
        trigger = Div(
            Raw(_GLOBE_SVG),
            current_display,
            tabindex="0",
            role="button",
            cls=f"btn btn-ghost btn-{size} gap-1",
        )

        locale_buttons: list[Any] = []
        for loc in locale_list:
            display_name = _LOCALE_DISPLAY_NAMES.get(loc, loc)
            active_cls = " btn-active" if loc == current else ""
            locale_buttons.append(
                Raw(
                    f'<button onclick="kokageSwitchLocale(\'{loc}\')"'
                    f' class="btn btn-ghost btn-sm justify-start w-full{active_cls}">'
                    f'<span class="text-xs">{display_name}</span></button>'
                )
            )

        dropdown_content = Div(
            Div(*locale_buttons, cls="grid grid-cols-1 gap-1"),
            tabindex="0",
            cls="dropdown-content bg-base-200 rounded-box z-10 w-44 p-2 shadow-lg",
        )

        script_code = (
            "window.kokageSwitchLocale=function(loc){"
            "var u=new URL(window.location.href);"
            "u.searchParams.set('lang',loc);"
            "window.location.href=u.toString();"
            "};"
        )

        cls = "dropdown dropdown-end"
        if attrs.get("cls"):
            cls += f" {attrs.pop('cls')}"
        attrs["cls"] = cls

        super().__init__(
            trigger, dropdown_content, Script(Raw(script_code)), **attrs
        )
