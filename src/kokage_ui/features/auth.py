"""Authentication & authorization UI components.

Provides pre-built login/register forms, user menus, role-based
rendering, and a `protected` decorator for auth-gated pages.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable

from kokage_ui.components import Alert, DaisyButton, _merge_cls
from kokage_ui.elements import (
    A,
    Component,
    Div,
    Form,
    H2,
    Hr,
    Img,
    Input,
    Label,
    Li,
    P,
    Span,
    Ul,
)


# ========================================
# LoginForm
# ========================================


class LoginForm(Component):
    """Pre-built login form card with DaisyUI styling.

    Generates a centered card with username/email and password fields,
    optional links for registration and password recovery.

    Args:
        action: Form action URL.
        method: Form method.
        title: Form title.
        username_label: Label for the username/email field.
        username_field: Name attribute for the username field.
        password_label: Label for the password field.
        password_field: Name attribute for the password field.
        submit_text: Submit button text.
        submit_color: DaisyUI button color.
        register_url: URL to registration page.
        register_text: Registration link text.
        forgot_url: URL to forgot password page.
        forgot_text: Forgot password link text.
        error: Error message to display.
        use_email: Use email input type for the username field.
    """

    tag = "div"

    def __init__(
        self,
        *,
        action: str = "/login",
        method: str = "post",
        title: str = "Login",
        username_label: str = "Username",
        username_field: str = "username",
        password_label: str = "Password",
        password_field: str = "password",
        submit_text: str = "Login",
        submit_color: str = "primary",
        register_url: str | None = None,
        register_text: str = "Create account",
        forgot_url: str | None = None,
        forgot_text: str = "Forgot password?",
        error: str | None = None,
        use_email: bool = False,
        **attrs: Any,
    ) -> None:
        attrs["cls"] = _merge_cls(
            "flex items-center justify-center min-h-screen", attrs.get("cls")
        )

        form_children: list[Any] = []

        # Error alert
        if error:
            form_children.append(Alert(error, variant="error", cls="mb-4"))

        # Username/email field
        input_type = "email" if use_email else "text"
        form_children.append(
            Div(
                Label(Span(username_label, cls="label-text"), cls="label"),
                Input(
                    type=input_type,
                    name=username_field,
                    placeholder=username_label,
                    cls="input input-bordered w-full",
                    required=True,
                ),
                cls="form-control w-full",
            )
        )

        # Password field
        password_extras: list[Any] = []
        if forgot_url:
            password_extras.append(
                Label(
                    A(
                        forgot_text,
                        href=forgot_url,
                        cls="label-text-alt link link-hover",
                    ),
                    cls="label",
                )
            )

        form_children.append(
            Div(
                Label(Span(password_label, cls="label-text"), cls="label"),
                Input(
                    type="password",
                    name=password_field,
                    placeholder=password_label,
                    cls="input input-bordered w-full",
                    required=True,
                ),
                *password_extras,
                cls="form-control w-full",
            )
        )

        # Submit button
        form_children.append(
            Div(
                DaisyButton(
                    submit_text, color=submit_color, type="submit", cls="w-full"
                ),
                cls="form-control mt-4",
            )
        )

        # Build card content
        card_children: list[Any] = [
            H2(title, cls="card-title justify-center text-2xl"),
            Form(*form_children, action=action, method=method),
        ]

        # Register link
        if register_url:
            card_children.append(
                P(
                    A(
                        register_text,
                        href=register_url,
                        cls="link link-hover link-primary",
                    ),
                    cls="text-center mt-2 text-sm",
                )
            )

        card = Div(
            Div(*card_children, cls="card-body"),
            cls="card bg-base-100 shadow-xl w-full max-w-sm",
        )

        super().__init__(card, **attrs)


# ========================================
# RegisterForm
# ========================================


class RegisterForm(Component):
    """Pre-built registration form card with DaisyUI styling.

    Generates a centered card with customizable fields and optional
    password confirmation.

    Args:
        action: Form action URL.
        method: Form method.
        title: Form title.
        fields: List of (name, label, input_type) tuples.
            Default: username, email, password.
        submit_text: Submit button text.
        submit_color: DaisyUI button color.
        login_url: URL to login page.
        login_text: Login link text.
        error: Error message to display.
        confirm_password: Add password confirmation field.
    """

    tag = "div"

    def __init__(
        self,
        *,
        action: str = "/register",
        method: str = "post",
        title: str = "Create Account",
        fields: list[tuple[str, str, str]] | None = None,
        submit_text: str = "Register",
        submit_color: str = "primary",
        login_url: str | None = None,
        login_text: str = "Already have an account?",
        error: str | None = None,
        confirm_password: bool = True,
        **attrs: Any,
    ) -> None:
        attrs["cls"] = _merge_cls(
            "flex items-center justify-center min-h-screen", attrs.get("cls")
        )

        if fields is None:
            fields = [
                ("username", "Username", "text"),
                ("email", "Email", "email"),
                ("password", "Password", "password"),
            ]

        if confirm_password:
            fields = list(fields) + [
                ("password_confirm", "Confirm Password", "password")
            ]

        form_children: list[Any] = []

        if error:
            form_children.append(Alert(error, variant="error", cls="mb-4"))

        for name, label, input_type in fields:
            form_children.append(
                Div(
                    Label(Span(label, cls="label-text"), cls="label"),
                    Input(
                        type=input_type,
                        name=name,
                        placeholder=label,
                        cls="input input-bordered w-full",
                        required=True,
                    ),
                    cls="form-control w-full",
                )
            )

        form_children.append(
            Div(
                DaisyButton(
                    submit_text, color=submit_color, type="submit", cls="w-full"
                ),
                cls="form-control mt-4",
            )
        )

        card_children: list[Any] = [
            H2(title, cls="card-title justify-center text-2xl"),
            Form(*form_children, action=action, method=method),
        ]

        if login_url:
            card_children.append(
                P(
                    A(
                        login_text,
                        href=login_url,
                        cls="link link-hover link-primary",
                    ),
                    cls="text-center mt-2 text-sm",
                )
            )

        card = Div(
            Div(*card_children, cls="card-body"),
            cls="card bg-base-100 shadow-xl w-full max-w-sm",
        )

        super().__init__(card, **attrs)


# ========================================
# UserMenu
# ========================================


class UserMenu(Component):
    """User dropdown menu for navigation bars.

    Shows username with optional avatar and a dropdown menu.
    Typically placed in NavBar's ``end`` slot.

    Args:
        username: Display name.
        avatar_url: URL for circular avatar image.
        logout_url: Logout URL.
        logout_text: Logout link text.
        menu_items: Additional menu items as (label, href) tuples.
    """

    tag = "div"

    def __init__(
        self,
        *,
        username: str,
        avatar_url: str | None = None,
        logout_url: str = "/logout",
        logout_text: str = "Logout",
        menu_items: list[tuple[str, str]] | None = None,
        **attrs: Any,
    ) -> None:
        attrs["cls"] = _merge_cls("dropdown dropdown-end", attrs.get("cls"))

        # Build trigger button
        trigger_children: list[Any] = []
        if avatar_url:
            trigger_children.append(
                Div(
                    Div(
                        Img(src=avatar_url, alt=username, cls="w-8 rounded-full"),
                        cls="w-8 rounded-full",
                    ),
                    cls="avatar",
                )
            )
        trigger_children.append(Span(username))

        trigger = Div(
            *trigger_children,
            tabindex="0",
            role="button",
            cls="btn btn-ghost gap-2",
        )

        # Build menu items
        items: list[Any] = []
        if menu_items:
            for label, href in menu_items:
                items.append(Li(A(label, href=href)))

        # Divider before logout (only if there are other items)
        if items:
            items.append(Hr())

        items.append(Li(A(logout_text, href=logout_url, cls="text-error")))

        menu = Ul(
            *items,
            tabindex="0",
            cls="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow",
        )

        super().__init__(trigger, menu, **attrs)


# ========================================
# RoleGuard
# ========================================


class RoleGuard(Component):
    """Conditionally renders children based on user role.

    Server-side role check — content is only included in HTML output
    when the user has the required role(s).

    Args:
        *children: Content to render when authorized.
        role: Required role or list of roles (any match grants access).
        user_role: Current user's role or list of roles.
        fallback: Content to render when not authorized (default: nothing).
    """

    tag = "div"

    def __init__(
        self,
        *children: Any,
        role: str | list[str],
        user_role: str | list[str] | None,
        fallback: Any = None,
        **attrs: Any,
    ) -> None:
        required = {role} if isinstance(role, str) else set(role)

        if user_role is None:
            has_role = False
        elif isinstance(user_role, str):
            has_role = user_role in required
        else:
            has_role = bool(required & set(user_role))

        self._should_render = has_role or fallback is not None

        if has_role:
            super().__init__(*children, **attrs)
        elif fallback is not None:
            super().__init__(fallback, **attrs)
        else:
            super().__init__(**attrs)

    def render(self) -> str:
        if not self._should_render:
            return ""
        return super().render()


# ========================================
# protected decorator
# ========================================


def protected(
    auth_check: Callable,
    *,
    redirect_to: str = "/login",
    role: str | list[str] | None = None,
    role_key: str = "role",
) -> Callable:
    """Decorator that requires authentication for a page/fragment.

    Use with ``@ui.page()`` or ``@ui.fragment()``:

    .. code-block:: python

        async def get_user(request: Request) -> dict | None:
            token = request.cookies.get("token")
            if not token:
                return None
            return {"username": "alice", "role": "admin"}

        @ui.page("/dashboard")
        @protected(get_user, redirect_to="/login")
        async def dashboard(request: Request):
            user = request.state.user
            return Page(H1(f"Hello, {user['username']}"))

    Args:
        auth_check: Callable(Request) → user data or None.
            Can be sync or async.
        redirect_to: URL to redirect unauthenticated users.
        role: Required role(s) for authorization (403 if missing).
        role_key: Key to extract role from user data (for dicts)
            or attribute name (for objects).
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(**kwargs: Any) -> Any:
            from starlette.responses import RedirectResponse

            # Find request in kwargs
            request = kwargs.get("request")
            if request is None:
                raise ValueError(
                    "protected() requires the endpoint to accept a 'request' parameter"
                )

            # Run auth check
            user = auth_check(request)
            if inspect.isawaitable(user):
                user = await user

            if user is None:
                return RedirectResponse(redirect_to, status_code=302)

            # Role check
            if role is not None:
                required = {role} if isinstance(role, str) else set(role)
                if isinstance(user, dict):
                    user_roles = user.get(role_key, "")
                else:
                    user_roles = getattr(user, role_key, "")

                if isinstance(user_roles, str):
                    user_roles = {user_roles}
                else:
                    user_roles = set(user_roles)

                if not (required & user_roles):
                    from fastapi import HTTPException

                    raise HTTPException(status_code=403, detail="Forbidden")

            request.state.user = user
            result = func(**kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result

        return wrapper

    return decorator
