"""htmx pattern helpers.

Common htmx patterns as Python components.
"""

from __future__ import annotations

from typing import Any

from kokage_ui.elements import Component, Span


class HxSwapOOB(Component):
    """Out-of-Band Swap component.

    Updates elements outside the main target using hx-swap-oob.

    Args:
        *children: Content to insert.
        target_id: ID of the element to update.
        swap: Swap method (default: "true" = innerHTML).
    """

    tag = "div"

    def __init__(self, *children: Any, target_id: str, swap: str = "true", **attrs: Any) -> None:
        attrs["id"] = target_id
        attrs["hx_swap_oob"] = swap
        super().__init__(*children, **attrs)


class AutoRefresh(Component):
    """Auto-refresh component.

    Polls the server at a regular interval using hx-trigger="every Ns".

    Args:
        *children: Initial content (shown before first load).
        url: URL to poll.
        interval: Refresh interval in seconds.
        target: Target selector (default: self).
        swap: Swap method (default: "innerHTML").
    """

    tag = "div"

    def __init__(
        self,
        *children: Any,
        url: str,
        interval: int = 5,
        target: str | None = None,
        swap: str = "innerHTML",
        **attrs: Any,
    ) -> None:
        attrs["hx_get"] = url
        attrs["hx_trigger"] = f"every {interval}s"
        attrs["hx_swap"] = swap
        if target:
            attrs["hx_target"] = target
        super().__init__(*children, **attrs)


class SearchFilter(Component):
    """Search filter with debounce.

    Triggers server-side search on keyup with delay using
    hx-trigger="keyup changed delay:Nms".

    Args:
        url: Search endpoint URL.
        target: Result display selector.
        placeholder: Input placeholder text.
        name: Input name attribute.
        delay: Debounce delay in milliseconds.
    """

    tag = "input"

    def __init__(
        self,
        *,
        url: str,
        target: str,
        placeholder: str = "Search...",
        name: str = "q",
        delay: int = 300,
        **attrs: Any,
    ) -> None:
        attrs["type"] = "search"
        attrs["name"] = name
        attrs["placeholder"] = placeholder
        attrs["hx_get"] = url
        attrs["hx_trigger"] = f"keyup changed delay:{delay}ms"
        attrs["hx_target"] = target
        attrs.setdefault("cls", "input")
        super().__init__(**attrs)


class InfiniteScroll(Component):
    """Infinite scroll trigger.

    Loads next page when the element enters the viewport using
    hx-trigger="revealed".

    Args:
        url: Next page URL.
        target: Insert target selector.
        swap: Swap method (default: "beforeend").
        indicator: Loading indicator component.
    """

    tag = "div"

    def __init__(
        self,
        *,
        url: str,
        target: str | None = None,
        swap: str = "beforeend",
        indicator: Any = None,
        **attrs: Any,
    ) -> None:
        attrs["hx_get"] = url
        attrs["hx_trigger"] = "revealed"
        attrs["hx_swap"] = swap
        if target:
            attrs["hx_target"] = target

        children: list[Any] = []
        if indicator:
            children.append(indicator)
        else:
            children.append(Span("Loading...", cls="loading loading-spinner"))

        super().__init__(*children, **attrs)


class SSEStream(Component):
    """Server-Sent Events stream receiver.

    Uses htmx SSE extension for real-time data. Requires Page(include_sse=True).

    Args:
        *children: Initial content.
        url: SSE endpoint URL.
        event: SSE event name to listen for.
        swap: Swap method (default: "innerHTML").
    """

    tag = "div"

    def __init__(
        self,
        *children: Any,
        url: str,
        event: str = "message",
        swap: str = "innerHTML",
        **attrs: Any,
    ) -> None:
        attrs["hx_ext"] = "sse"
        attrs["sse_connect"] = url
        attrs["sse_swap"] = event
        attrs["hx_swap"] = swap
        super().__init__(*children, **attrs)


class DependentField(Component):
    """Generic wrapper that reloads content when a parent field changes.

    Any content inside is replaced via htmx when the watched field changes.

    Args:
        *children: Initial content (shown before first load).
        depends_on: Name of the parent field to watch.
        url: URL to fetch new content from.
        swap: htmx swap method.
        target: htmx target selector (default: self).
    """

    tag = "div"

    def __init__(
        self,
        *children: Any,
        depends_on: str,
        url: str,
        swap: str = "innerHTML",
        target: str | None = None,
        **attrs: Any,
    ) -> None:
        attrs["hx_get"] = url
        attrs["hx_trigger"] = f"change from:[name='{depends_on}']"
        attrs["hx_include"] = f"[name='{depends_on}']"
        attrs["hx_swap"] = swap
        if target:
            attrs["hx_target"] = target
        super().__init__(*children, **attrs)


class ConfirmDelete(Component):
    """Delete button with confirmation dialog.

    Combines hx-confirm + hx-delete pattern.

    Args:
        *children: Button text.
        url: DELETE endpoint URL.
        confirm_message: Confirmation dialog message.
        target: Target selector to update after deletion.
        swap: Swap method (default: "outerHTML").
    """

    tag = "button"

    def __init__(
        self,
        *children: Any,
        url: str,
        confirm_message: str = "Are you sure?",
        target: str | None = None,
        swap: str = "outerHTML",
        **attrs: Any,
    ) -> None:
        attrs["hx_delete"] = url
        attrs["hx_confirm"] = confirm_message
        attrs["hx_swap"] = swap
        if target:
            attrs["hx_target"] = target
        attrs.setdefault("cls", "btn btn-error btn-outline")
        super().__init__(*children, **attrs)
