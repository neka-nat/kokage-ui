"""Test helpers for kokage-ui.

Provides utilities for rendering components, asserting HTML content,
and creating test FastAPI apps.

Usage:
    from kokage_ui.dev.testing import rendered, assert_response, make_app

    # Component assertions
    rendered(Card("Hello", title="My Card")).has("card-body", "My Card")

    # Response assertions
    assert_response(client.get("/items")).is_ok().has("Widget", "table")
"""

from __future__ import annotations

import re
from typing import Any


def render(component: Any) -> str:
    """Render a Component, Page, or any object to HTML string.

    Normalizes the two idioms: str(comp) and comp.render().
    """
    if hasattr(component, "render"):
        return component.render()
    if hasattr(component, "__html__"):
        return component.__html__()
    return str(component)


class HTMLAssertions:
    """HTML string wrapper with assertion helpers.

    Usage:
        doc = rendered(Card("Hello", title="My Card"))
        doc.has("card-body", "My Card")
        doc.has_not("hidden")
        doc.has_element("img", src="/photo.jpg")
        doc.has_count("btn", 2)
    """

    def __init__(self, html: str) -> None:
        self.html = html

    # --- Basic containment ---

    def has(self, *fragments: str) -> HTMLAssertions:
        """Assert all fragments are present in the HTML."""
        for frag in fragments:
            assert frag in self.html, (
                f"Expected to find {frag!r} in HTML:\n{self.html[:500]}"
            )
        return self

    def has_not(self, *fragments: str) -> HTMLAssertions:
        """Assert none of the fragments are present."""
        for frag in fragments:
            assert frag not in self.html, (
                f"Expected {frag!r} to NOT be in HTML:\n{self.html[:500]}"
            )
        return self

    # --- Count ---

    def has_count(self, fragment: str, count: int) -> HTMLAssertions:
        """Assert fragment appears exactly `count` times."""
        actual = self.html.count(fragment)
        assert actual == count, (
            f"Expected {fragment!r} to appear {count} times, found {actual}"
        )
        return self

    # --- Element-level assertions (attribute matching) ---

    def has_element(self, tag: str, **attrs: str) -> HTMLAssertions:
        """Assert an element with the given tag and attributes exists.

        Uses regex to find <tag ... attr="value" ...>.

        Usage:
            doc.has_element("input", type="file", accept="image/*")
            doc.has_element("div", id="main")
        """
        pattern = rf"<{re.escape(tag)}\b[^>]*>"
        matches = re.findall(pattern, self.html)
        for match in matches:
            if all(
                re.search(rf'{re.escape(k)}="{re.escape(v)}"', match)
                for k, v in attrs.items()
            ):
                return self
        attrs_str = ", ".join(f'{k}="{v}"' for k, v in attrs.items())
        raise AssertionError(
            f"No <{tag} {attrs_str}> found in HTML:\n{self.html[:500]}"
        )

    def has_no_element(self, tag: str, **attrs: str) -> HTMLAssertions:
        """Assert no element with the given tag and attributes exists."""
        pattern = rf"<{re.escape(tag)}\b[^>]*>"
        matches = re.findall(pattern, self.html)
        for match in matches:
            if all(
                re.search(rf'{re.escape(k)}="{re.escape(v)}"', match)
                for k, v in attrs.items()
            ):
                attrs_str = ", ".join(f'{k}="{v}"' for k, v in attrs.items())
                raise AssertionError(
                    f"Found unexpected <{tag} {attrs_str}> in HTML:\n{self.html[:500]}"
                )
        return self

    # --- Tag presence ---

    def has_tag(self, tag: str) -> HTMLAssertions:
        """Assert at least one <tag...> exists."""
        assert re.search(rf"<{re.escape(tag)}\b", self.html), (
            f"No <{tag}> found in HTML:\n{self.html[:500]}"
        )
        return self

    def has_no_tag(self, tag: str) -> HTMLAssertions:
        """Assert no <tag...> exists."""
        assert not re.search(rf"<{re.escape(tag)}\b", self.html), (
            f"Unexpected <{tag}> found in HTML:\n{self.html[:500]}"
        )
        return self


def rendered(component: Any) -> HTMLAssertions:
    """Render a component and return an HTMLAssertions wrapper.

    Usage:
        rendered(Card("Hello")).has("card-body", "Hello").has_not("hidden")
    """
    return HTMLAssertions(render(component))


def make_app(**kwargs: Any) -> tuple:
    """Create a minimal FastAPI + KokageUI app for testing.

    Returns (app, ui) tuple.
    """
    from fastapi import FastAPI

    from kokage_ui.core import KokageUI

    app = FastAPI()
    ui = KokageUI(app)
    return app, ui


def make_client(app: Any) -> Any:
    """Create a TestClient for the given app.

    Returns starlette.testclient.TestClient.
    """
    from starlette.testclient import TestClient

    return TestClient(app)


class ResponseAssertions:
    """HTTP response wrapper with assertion helpers."""

    def __init__(self, response: Any) -> None:
        self.response = response
        self.status_code = response.status_code
        self.text = response.text

    def is_ok(self) -> ResponseAssertions:
        """Assert status code is 200."""
        assert self.status_code == 200, f"Expected 200, got {self.status_code}"
        return self

    def is_status(self, code: int) -> ResponseAssertions:
        """Assert status code matches."""
        assert self.status_code == code, f"Expected {code}, got {self.status_code}"
        return self

    def has(self, *fragments: str) -> ResponseAssertions:
        """Assert all fragments are present in the response body."""
        for frag in fragments:
            assert frag in self.text, (
                f"Expected {frag!r} in response body:\n{self.text[:500]}"
            )
        return self

    def has_not(self, *fragments: str) -> ResponseAssertions:
        """Assert none of the fragments are present in the response body."""
        for frag in fragments:
            assert frag not in self.text, (
                f"Unexpected {frag!r} in response body:\n{self.text[:500]}"
            )
        return self

    def html(self) -> HTMLAssertions:
        """Convert to HTMLAssertions for element-level inspection."""
        return HTMLAssertions(self.text)


def assert_response(response: Any) -> ResponseAssertions:
    """Wrap an HTTP response for fluent assertion chaining."""
    return ResponseAssertions(response)
