"""FastAPI integration for kokage.

Provides KokageUI class to mount UI on a FastAPI app.
"""

from __future__ import annotations

import functools
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from kokage_ui.elements import Component
from kokage_ui.page import Page

if TYPE_CHECKING:
    from pydantic import BaseModel

    from kokage_ui.data.crud import Storage

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

    def __init__(
        self,
        app: FastAPI,
        prefix: str = "/_kokage",
        debug: bool = False,
        locale: str | None = None,
        translations: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.app = app
        self.prefix = prefix
        self.debug = debug
        self._routes: list[dict] = []
        self._setup_static_files()
        if locale is not None:
            from kokage_ui.features.i18n import LocaleMiddleware, configure

            configure(default_locale=locale, translations=translations)
            self.app.add_middleware(LocaleMiddleware)
        if self.debug:
            from kokage_ui.dev.toolbar import DevToolbarMiddleware

            self.app.add_middleware(DevToolbarMiddleware, routes=self._routes)

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
        layout: Any = None,
        title: str = "",
        **route_kwargs: Any,
    ) -> Callable:
        """Decorator for full-page HTML routes.

        The decorated function should return a Page, Component, or str.
        The return value is automatically converted to an HTMLResponse.

        Args:
            path: URL path.
            methods: HTTP methods (default: ["GET"]).
            layout: Optional Layout instance to wrap the result.
            title: Page title (used with layout).
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
                # Allow Response objects to pass through (e.g., RedirectResponse from @protected)
                if isinstance(result, Response):
                    return result
                if layout is not None and not isinstance(result, Page):
                    result = layout.wrap(result, title)
                html_str = _to_html_string(result)
                return HTMLResponse(content=html_str)

            if self.debug:
                self._routes.append({"path": path, "methods": methods, "type": "page", "name": func.__name__})
            self.app.add_api_route(
                path,
                wrapper,
                methods=methods,
                response_class=HTMLResponse,
                **route_kwargs,
            )
            return wrapper

        return decorator

    def crud(
        self,
        prefix: str,
        *,
        model: type[BaseModel],
        storage: Storage,
        id_field: str = "id",
        per_page: int = 20,
        title: str | None = None,
        exclude_fields: list[str] | None = None,
        table_exclude: list[str] | None = None,
        form_exclude: list[str] | None = None,
        page_wrapper: Callable[..., Any] | None = None,
        layout: Any = None,
        theme: str = "light",
        file_handler: Callable | None = None,
        sortable: bool = False,
    ) -> None:
        """Register full CRUD routes for a Pydantic model.

        Args:
            prefix: URL prefix (e.g., "/users").
            model: Pydantic BaseModel class.
            storage: Storage backend.
            id_field: Name of the ID field.
            per_page: Items per page.
            title: Display title.
            exclude_fields: Fields to exclude from all views.
            table_exclude: Fields to exclude from table view.
            form_exclude: Fields to exclude from forms.
            page_wrapper: Optional callable(content, title) → Page.
            layout: Optional Layout instance (used as page_wrapper if page_wrapper not set).
            theme: DaisyUI theme name.
            file_handler: Async callback (field_name, UploadFile) → URL string.
            sortable: Enable drag & drop reordering with SortableJS.
        """
        from kokage_ui.data.crud import CRUDRouter

        if layout is not None and page_wrapper is None:
            page_wrapper = layout.wrap

        CRUDRouter(
            self.app,
            prefix,
            model,
            storage,
            id_field=id_field,
            per_page=per_page,
            title=title,
            exclude_fields=exclude_fields,
            table_exclude=table_exclude,
            form_exclude=form_exclude,
            page_wrapper=page_wrapper,
            theme=theme,
            file_handler=file_handler,
            sortable=sortable,
        )

        if self.debug:
            crud_routes = [
                (["GET"], prefix, "list"),
                (["GET"], f"{prefix}/_list", "list_fragment"),
                (["GET"], f"{prefix}/new", "create_form"),
                (["POST"], f"{prefix}/new", "create"),
                (["GET"], f"{prefix}/{{id}}", "detail"),
                (["GET"], f"{prefix}/{{id}}/edit", "edit_form"),
                (["POST"], f"{prefix}/{{id}}/edit", "update"),
                (["DELETE"], f"{prefix}/{{id}}", "delete"),
            ]
            for methods, p, name in crud_routes:
                self._routes.append({"path": p, "methods": methods, "type": "crud", "name": name})

    def validate(
        self,
        path: str,
        model: type[BaseModel],
        *,
        exclude: set[str] | list[str] | None = None,
        trigger: str = "change",
        delay: int = 500,
    ) -> None:
        """Register per-field validation endpoints for a Pydantic model.

        For each field, registers POST {path}/{field_name} that validates
        the field value and returns the field wrapper HTML with error/success styling.

        Args:
            path: Base URL path (e.g., "/validate").
            model: Pydantic BaseModel class.
            exclude: Field names to exclude from validation.
            trigger: htmx trigger event.
            delay: Debounce delay in ms.
        """
        from pydantic import ValidationError
        from pydantic.fields import FieldInfo

        from kokage_ui.models import _SENTINEL, _field_to_component, _filter_fields

        fields = _filter_fields(model, include=None, exclude=exclude)
        trigger_str = f"{trigger} delay:{delay}ms" if delay > 0 else trigger

        for field_name, field_info in fields:

            def _make_handler(name: str, fi: FieldInfo) -> Any:
                async def handler(request: Request) -> HTMLResponse:
                    form_data = await request.form()
                    raw_data = dict(form_data)

                    error_msg = None
                    try:
                        model.model_validate(raw_data)
                    except ValidationError as e:
                        for err in e.errors():
                            loc = err.get("loc", ())
                            if loc and str(loc[0]) == name:
                                error_msg = err.get("msg", "Invalid value")
                                break

                    component = _field_to_component(
                        name,
                        fi,
                        value=raw_data.get(name, _SENTINEL),
                        error_message=error_msg,
                        field_id=f"field-{name}",
                        extra_input_attrs={
                            "hx_post": f"{path}/{name}",
                            "hx_trigger": trigger_str,
                            "hx_target": f"#field-{name}",
                            "hx_swap": "outerHTML",
                        },
                    )
                    return HTMLResponse(content=component.render())

                return handler

            if self.debug:
                self._routes.append({"path": f"{path}/{field_name}", "methods": ["POST"], "type": "validate", "name": field_name})
            self.app.add_api_route(
                f"{path}/{field_name}",
                _make_handler(field_name, field_info),
                methods=["POST"],
                response_class=HTMLResponse,
            )

    def multistep(
        self,
        path: str,
        *,
        model: type[BaseModel],
        steps: list[Any],
        action: str,
    ) -> None:
        """Register multi-step form navigation endpoints.

        Registers:
        - POST {path}/{step}: validate step and return next step form
        - POST {path}/goto/{step}: go to step without validation

        Args:
            path: Base URL path (e.g., "/register/step").
            model: Pydantic BaseModel class.
            steps: List of FormStep instances.
            action: Form action URL for final submission.
        """
        from pydantic import ValidationError

        from kokage_ui.features.forms import MultiStepForm

        async def validate_step(request: Request, step: int) -> HTMLResponse:
            form_data = await request.form()
            raw_data = dict(form_data)

            current_fields = steps[step].fields
            try:
                model.model_validate(raw_data)
            except ValidationError as e:
                step_errors = [
                    err
                    for err in e.errors()
                    if err.get("loc") and str(err["loc"][0]) in current_fields
                ]
                if step_errors:
                    form = MultiStepForm(
                        model,
                        steps=steps,
                        current_step=step,
                        validate_url=path,
                        action=action,
                        values=raw_data,
                        errors=step_errors,
                    )
                    return HTMLResponse(content=form.render())

            next_step = min(step + 1, len(steps) - 1)
            form = MultiStepForm(
                model,
                steps=steps,
                current_step=next_step,
                validate_url=path,
                action=action,
                values=raw_data,
            )
            return HTMLResponse(content=form.render())

        async def goto_step(request: Request, step: int) -> HTMLResponse:
            form_data = await request.form()
            raw_data = dict(form_data)
            form = MultiStepForm(
                model,
                steps=steps,
                current_step=step,
                validate_url=path,
                action=action,
                values=raw_data,
            )
            return HTMLResponse(content=form.render())

        if self.debug:
            self._routes.append({"path": f"{path}/{{step}}", "methods": ["POST"], "type": "multistep", "name": "validate_step"})
            self._routes.append({"path": f"{path}/goto/{{step}}", "methods": ["POST"], "type": "multistep", "name": "goto_step"})
        self.app.add_api_route(
            f"{path}/{{step}}",
            validate_step,
            methods=["POST"],
            response_class=HTMLResponse,
        )
        self.app.add_api_route(
            f"{path}/goto/{{step}}",
            goto_step,
            methods=["POST"],
            response_class=HTMLResponse,
        )

    def chat(
        self,
        path: str,
        *,
        placeholder: str = "メッセージを入力...",
        send_label: str = "送信",
        assistant_name: str = "Assistant",
        user_name: str = "You",
        height: str = "600px",
        title: str = "Chat",
        layout: Any = None,
    ) -> Callable:
        """Decorator for AI chat endpoints.

        Registers both a page route (GET) with ChatView and an API
        endpoint (POST) for SSE streaming.  The decorated function
        receives ``message: str`` and should be an async generator
        that yields string tokens.

        Example::

            @ui.chat("/chat")
            async def my_chat(message: str):
                async for token in call_llm(message):
                    yield token

        Args:
            path: URL path.
            placeholder: Input field placeholder text.
            send_label: Submit button label.
            assistant_name: Display name for assistant messages.
            user_name: Display name for user messages.
            height: CSS height for the chat container.
            title: Page title.
            layout: Optional Layout instance to wrap the page.
        """

        def decorator(func: Callable) -> Callable:
            from kokage_ui.ai.chat import ChatView, chat_stream

            api_path = f"{path}/send"

            chat_view = ChatView(
                send_url=api_path,
                placeholder=placeholder,
                send_label=send_label,
                assistant_name=assistant_name,
                user_name=user_name,
                height=height,
            )

            page_content = Page(chat_view, title=title)

            @self.page(path, layout=layout, title=title)
            def _chat_page():
                return page_content

            async def _chat_api(request: Request) -> Response:
                data = await request.json()
                message = data.get("message", "")
                return chat_stream(func(message))

            self.app.add_api_route(
                api_path,
                _chat_api,
                methods=["POST"],
            )

            if self.debug:
                self._routes.append({"path": api_path, "methods": ["POST"], "type": "chat", "name": func.__name__})

            return func

        return decorator

    def agent(
        self,
        path: str,
        *,
        placeholder: str = "メッセージを入力...",
        send_label: str = "送信",
        agent_name: str = "Agent",
        user_name: str = "You",
        height: str = "700px",
        show_metrics: bool = True,
        show_status: bool = True,
        tool_expanded: bool = False,
        title: str = "Agent",
        layout: Any = None,
    ) -> Callable:
        """Decorator for AI agent endpoints.

        Registers both a page route (GET) with AgentView and an API
        endpoint (POST) for SSE streaming.  The decorated function
        receives ``message: str`` and should be an async generator
        that yields AgentEvent instances.

        Example::

            @ui.agent("/agent")
            async def my_agent(message: str):
                yield AgentEvent(type="text", content="Hello")
                yield AgentEvent(type="done")

        Args:
            path: URL path.
            placeholder: Input field placeholder text.
            send_label: Submit button label.
            agent_name: Display name for agent messages.
            user_name: Display name for user messages.
            height: CSS height for the container.
            show_metrics: Show metrics bar.
            show_status: Show status bar.
            tool_expanded: Default expand state for tool panels.
            title: Page title.
            layout: Optional Layout instance to wrap the page.
        """

        def decorator(func: Callable) -> Callable:
            from kokage_ui.ai.agent import AgentView, agent_stream

            api_path = f"{path}/send"

            agent_view = AgentView(
                send_url=api_path,
                placeholder=placeholder,
                send_label=send_label,
                agent_name=agent_name,
                user_name=user_name,
                height=height,
                show_metrics=show_metrics,
                show_status=show_status,
                tool_expanded=tool_expanded,
            )

            page_content = Page(agent_view, title=title)

            @self.page(path, layout=layout, title=title)
            def _agent_page():
                return page_content

            async def _agent_api(request: Request) -> Response:
                data = await request.json()
                message = data.get("message", "")
                return agent_stream(func(message))

            self.app.add_api_route(
                api_path,
                _agent_api,
                methods=["POST"],
            )

            if self.debug:
                self._routes.append({"path": api_path, "methods": ["POST"], "type": "agent", "name": func.__name__})

            return func

        return decorator

    def threaded_agent(
        self,
        path: str,
        *,
        store: Any,
        threads_prefix: str | None = None,
        placeholder: str = "メッセージを入力...",
        send_label: str = "送信",
        stop_label: str = "停止",
        agent_name: str = "Agent",
        user_name: str = "You",
        height: str = "100vh",
        show_metrics: bool = True,
        show_status: bool = True,
        tool_expanded: bool = False,
        new_thread_label: str = "+ New Thread",
        title: str = "Agent",
        layout: Any = None,
    ) -> Callable:
        """Decorator for threaded AI agent endpoints.

        Registers a page with ThreadedAgentView, mounts the ConversationStore
        REST API, and creates a POST endpoint for SSE streaming.
        The decorated function receives ``message: str`` and ``thread_id: str``
        and should be an async generator yielding AgentEvent instances.

        Example::

            store = InMemoryConversationStore()

            @ui.threaded_agent("/agent", store=store)
            async def my_agent(message: str, thread_id: str):
                yield AgentEvent(type="text", content="Hello")
                yield AgentEvent(type="done")

        Args:
            path: URL path.
            store: ConversationStore instance.
            threads_prefix: REST API prefix for threads (default: "{path}/threads").
            placeholder: Input field placeholder text.
            send_label: Submit button label.
            stop_label: Stop button label shown during streaming.
            agent_name: Display name for agent messages.
            user_name: Display name for user messages.
            height: CSS height for the container.
            show_metrics: Show metrics bar.
            show_status: Show status bar.
            tool_expanded: Default expand state for tool panels.
            new_thread_label: Label for new thread button.
            title: Page title.
            layout: Optional Layout instance to wrap the page.
        """

        def decorator(func: Callable) -> Callable:
            from kokage_ui.ai.agent import agent_stream
            from kokage_ui.ai.threaded import ThreadedAgentView

            base = path.rstrip("/")
            api_path = f"{base}/send"
            t_prefix = threads_prefix or f"{base}/threads"

            # Mount ConversationStore REST API
            store.mount(self.app, prefix=t_prefix)

            threaded_view = ThreadedAgentView(
                send_url=api_path,
                threads_url=t_prefix,
                placeholder=placeholder,
                send_label=send_label,
                stop_label=stop_label,
                agent_name=agent_name,
                user_name=user_name,
                height=height,
                show_metrics=show_metrics,
                show_status=show_status,
                tool_expanded=tool_expanded,
                new_thread_label=new_thread_label,
            )

            page_content = Page(threaded_view, title=title)

            @self.page(path, layout=layout, title=title)
            def _threaded_agent_page():
                return page_content

            async def _threaded_agent_api(request: Request) -> Response:
                data = await request.json()
                message = data.get("message", "")
                thread_id = data.get("thread_id", "")
                return agent_stream(func(message, thread_id))

            self.app.add_api_route(
                api_path,
                _threaded_agent_api,
                methods=["POST"],
            )

            if self.debug:
                self._routes.append({"path": api_path, "methods": ["POST"], "type": "threaded_agent", "name": func.__name__})

            return func

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
                # Allow Response objects to pass through (e.g., RedirectResponse from @protected)
                if isinstance(result, Response):
                    return result
                html_str = _to_html_string(result)
                return HTMLResponse(content=html_str)

            if self.debug:
                self._routes.append({"path": path, "methods": methods, "type": "fragment", "name": func.__name__})
            self.app.add_api_route(
                path,
                wrapper,
                methods=methods,
                response_class=HTMLResponse,
                **route_kwargs,
            )
            return wrapper

        return decorator
