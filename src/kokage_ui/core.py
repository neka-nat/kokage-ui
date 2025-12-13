"""FastAPI integration for kokage.

Provides KokageUI class to mount UI on a FastAPI app.
"""

from __future__ import annotations

import functools
import inspect
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from kokage_ui.elements import Component
from kokage_ui.page import Page

STATIC_DIR = Path(__file__).parent / "static"


def _to_html_string(result: Any) -> str:
    """Convert various return types to HTML string."""
    if isinstance(result, str):
        return result
    if isinstance(result, (Page, Component)):
        return result.render()
    if hasattr(result, "__html__"):
        return result.__html__()
    if isinstance(result, (list, tuple)):
        return "".join(_to_html_string(item) for item in result)
    return str(result)


class KokageUI:
    """FastAPI integration for kokage UI.

    Mounts static files and provides page/fragment decorators.

    Example:
        app = FastAPI()
        ui = KokageUI(app)

        @ui.page("/")
        def index():
            return Page(H1("Hello"), title="Home")
    """

    def __init__(self, app: FastAPI, prefix: str = "/_kokage") -> None:
        self.app = app
        self.prefix = prefix
        self._setup_static_files()

    def _setup_static_files(self) -> None:
        """Mount htmx.min.js and other static files."""
        if STATIC_DIR.exists():
            self.app.mount(
                f"{self.prefix}/static",
                StaticFiles(directory=str(STATIC_DIR)),
                name="kokage_static",
            )

    def page(
        self,
        path: str,
        *,
        methods: list[str] | None = None,
        **route_kwargs: Any,
    ) -> Callable:
        """Decorator for full-page HTML routes.

        The decorated function should return a Page, Component, or str.
        The return value is automatically converted to an HTMLResponse.

        Args:
            path: URL path.
            methods: HTTP methods (default: ["GET"]).
            **route_kwargs: Additional args passed to FastAPI add_api_route().
        """
        if methods is None:
            methods = ["GET"]

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(**kwargs: Any) -> HTMLResponse:
                result = func(**kwargs)
                if inspect.isawaitable(result):
                    result = await result
                html_str = _to_html_string(result)
                return HTMLResponse(content=html_str)

            self.app.add_api_route(
                path,
                wrapper,
                methods=methods,
                response_class=HTMLResponse,
                **route_kwargs,
            )
            return wrapper

        return decorator

    def fragment(
        self,
        path: str,
        *,
        methods: list[str] | None = None,
        htmx_only: bool = True,
        **route_kwargs: Any,
    ) -> Callable:
        """Decorator for HTML fragment routes (htmx partial responses).

        Returns partial HTML for htmx requests. When htmx_only=True (default),
        non-htmx requests get a 403 response.

        Args:
            path: URL path.
            methods: HTTP methods (default: ["GET"]).
            htmx_only: Only allow htmx requests (default: True).
            **route_kwargs: Additional args passed to FastAPI add_api_route().
        """
        if methods is None:
            methods = ["GET"]

        def decorator(func: Callable) -> Callable:
            # Check if original function accepts 'request' parameter
            sig = inspect.signature(func)
            accepts_request = "request" in sig.parameters

            @functools.wraps(func)
            async def wrapper(request: Request, **kwargs: Any) -> HTMLResponse:
                if htmx_only and request.headers.get("hx-request") is None:
                    return HTMLResponse(
                        content="This endpoint only accepts htmx requests",
                        status_code=403,
                    )

                if accepts_request:
                    kwargs["request"] = request

                result = func(**kwargs)
                if inspect.isawaitable(result):
                    result = await result
                html_str = _to_html_string(result)
                return HTMLResponse(content=html_str)

            self.app.add_api_route(
                path,
                wrapper,
                methods=methods,
                response_class=HTMLResponse,
                **route_kwargs,
            )
            return wrapper

        return decorator
