"""Tests for Authentication & Authorization UI components."""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from kokage_ui import KokageUI, Page
from kokage_ui.features.auth import LoginForm, RegisterForm, RoleGuard, UserMenu, protected
from kokage_ui.elements import Div, H1


# ========================================
# LoginForm tests
# ========================================


class TestLoginForm:
    def test_renders_form(self):
        result = str(LoginForm())
        assert "<form" in result
        assert 'action="/login"' in result
        assert 'method="post"' in result

    def test_title(self):
        result = str(LoginForm(title="Sign In"))
        assert "Sign In" in result

    def test_username_field(self):
        result = str(LoginForm())
        assert 'name="username"' in result
        assert 'type="text"' in result

    def test_password_field(self):
        result = str(LoginForm())
        assert 'name="password"' in result
        assert 'type="password"' in result

    def test_use_email(self):
        result = str(LoginForm(use_email=True))
        assert 'type="email"' in result

    def test_custom_field_names(self):
        result = str(LoginForm(username_field="email", password_field="pass"))
        assert 'name="email"' in result
        assert 'name="pass"' in result

    def test_submit_button(self):
        result = str(LoginForm())
        assert "Login" in result
        assert "btn-primary" in result

    def test_custom_submit(self):
        result = str(LoginForm(submit_text="Sign In", submit_color="accent"))
        assert "Sign In" in result
        assert "btn-accent" in result

    def test_error_message(self):
        result = str(LoginForm(error="Invalid credentials"))
        assert "Invalid credentials" in result
        assert "alert-error" in result

    def test_no_error(self):
        result = str(LoginForm())
        assert "alert-error" not in result

    def test_register_link(self):
        result = str(LoginForm(register_url="/register"))
        assert 'href="/register"' in result
        assert "Create account" in result

    def test_no_register_link(self):
        result = str(LoginForm())
        assert "Create account" not in result

    def test_forgot_link(self):
        result = str(LoginForm(forgot_url="/forgot"))
        assert 'href="/forgot"' in result
        assert "Forgot password?" in result

    def test_no_forgot_link(self):
        result = str(LoginForm())
        assert "Forgot password?" not in result

    def test_custom_action(self):
        result = str(LoginForm(action="/api/login", method="post"))
        assert 'action="/api/login"' in result

    def test_card_structure(self):
        result = str(LoginForm())
        assert "card" in result
        assert "card-body" in result
        assert "shadow-xl" in result

    def test_centered_layout(self):
        result = str(LoginForm())
        assert "flex items-center justify-center min-h-screen" in result

    def test_required_fields(self):
        result = str(LoginForm())
        assert " required" in result

    def test_extra_cls(self):
        result = str(LoginForm(cls="bg-base-200"))
        assert "min-h-screen" in result
        assert "bg-base-200" in result


# ========================================
# RegisterForm tests
# ========================================


class TestRegisterForm:
    def test_renders_form(self):
        result = str(RegisterForm())
        assert "<form" in result
        assert 'action="/register"' in result

    def test_title(self):
        result = str(RegisterForm())
        assert "Create Account" in result

    def test_default_fields(self):
        result = str(RegisterForm())
        assert 'name="username"' in result
        assert 'name="email"' in result
        assert 'name="password"' in result

    def test_confirm_password_default(self):
        result = str(RegisterForm())
        assert 'name="password_confirm"' in result

    def test_no_confirm_password(self):
        result = str(RegisterForm(confirm_password=False))
        assert 'name="password_confirm"' not in result

    def test_custom_fields(self):
        fields = [
            ("name", "Full Name", "text"),
            ("email", "Email", "email"),
            ("password", "Password", "password"),
        ]
        result = str(RegisterForm(fields=fields, confirm_password=False))
        assert 'name="name"' in result
        assert 'name="email"' in result
        assert 'name="username"' not in result

    def test_error_message(self):
        result = str(RegisterForm(error="Email already exists"))
        assert "Email already exists" in result
        assert "alert-error" in result

    def test_login_link(self):
        result = str(RegisterForm(login_url="/login"))
        assert 'href="/login"' in result
        assert "Already have an account?" in result

    def test_no_login_link(self):
        result = str(RegisterForm())
        assert "Already have an account?" not in result

    def test_card_structure(self):
        result = str(RegisterForm())
        assert "card" in result
        assert "card-body" in result

    def test_submit_button(self):
        result = str(RegisterForm(submit_text="Sign Up", submit_color="success"))
        assert "Sign Up" in result
        assert "btn-success" in result


# ========================================
# UserMenu tests
# ========================================


class TestUserMenu:
    def test_renders_dropdown(self):
        result = str(UserMenu(username="Alice"))
        assert "dropdown" in result
        assert "dropdown-end" in result

    def test_username(self):
        result = str(UserMenu(username="Alice"))
        assert "Alice" in result

    def test_logout_link(self):
        result = str(UserMenu(username="Alice"))
        assert 'href="/logout"' in result
        assert "Logout" in result

    def test_custom_logout(self):
        result = str(UserMenu(username="A", logout_url="/signout", logout_text="Sign Out"))
        assert 'href="/signout"' in result
        assert "Sign Out" in result

    def test_avatar(self):
        result = str(UserMenu(username="Alice", avatar_url="/img/alice.png"))
        assert 'src="/img/alice.png"' in result
        assert "avatar" in result

    def test_no_avatar(self):
        result = str(UserMenu(username="Alice"))
        assert "avatar" not in result

    def test_menu_items(self):
        items = [("Profile", "/profile"), ("Settings", "/settings")]
        result = str(UserMenu(username="Alice", menu_items=items))
        assert 'href="/profile"' in result
        assert "Profile" in result
        assert 'href="/settings"' in result
        assert "Settings" in result

    def test_logout_has_error_class(self):
        result = str(UserMenu(username="Alice"))
        assert "text-error" in result

    def test_trigger_is_ghost_button(self):
        result = str(UserMenu(username="Alice"))
        assert "btn-ghost" in result

    def test_menu_dropdown_content(self):
        result = str(UserMenu(username="Alice"))
        assert "dropdown-content" in result
        assert "menu" in result


# ========================================
# RoleGuard tests
# ========================================


class TestRoleGuard:
    def test_renders_when_authorized(self):
        result = str(RoleGuard(Div("Secret"), role="admin", user_role="admin"))
        assert "Secret" in result

    def test_empty_when_unauthorized(self):
        result = str(RoleGuard(Div("Secret"), role="admin", user_role="viewer"))
        assert result == ""

    def test_empty_when_no_role(self):
        result = str(RoleGuard(Div("Secret"), role="admin", user_role=None))
        assert result == ""

    def test_fallback_when_unauthorized(self):
        result = str(
            RoleGuard(
                Div("Secret"),
                role="admin",
                user_role="viewer",
                fallback=Div("Access denied"),
            )
        )
        assert "Secret" not in result
        assert "Access denied" in result

    def test_multiple_required_roles(self):
        result = str(
            RoleGuard(Div("Content"), role=["admin", "editor"], user_role="editor")
        )
        assert "Content" in result

    def test_multiple_user_roles(self):
        result = str(
            RoleGuard(
                Div("Content"), role="admin", user_role=["viewer", "admin"]
            )
        )
        assert "Content" in result

    def test_no_match_multiple_roles(self):
        result = str(
            RoleGuard(
                Div("Content"), role=["admin", "editor"], user_role="viewer"
            )
        )
        assert result == ""


# ========================================
# protected decorator tests
# ========================================


class TestProtected:
    def _create_app(self, auth_func, *, role=None, role_key="role"):
        app = FastAPI()
        ui = KokageUI(app)

        @ui.page("/secret")
        @protected(auth_func, role=role, role_key=role_key)
        async def secret_page(request: Request):
            user = request.state.user
            name = user["username"] if isinstance(user, dict) else user.username
            return Page(H1(f"Hello {name}"), title="Secret")

        return TestClient(app)

    def test_redirects_when_unauthenticated(self):
        async def no_user(request):
            return None

        client = self._create_app(no_user)
        resp = client.get("/secret", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/login"

    def test_allows_authenticated_user(self):
        async def valid_user(request):
            return {"username": "alice", "role": "admin"}

        client = self._create_app(valid_user)
        resp = client.get("/secret")
        assert resp.status_code == 200
        assert "Hello alice" in resp.text

    def test_sets_request_state_user(self):
        user_data = {"username": "bob", "role": "editor"}

        async def get_user(request):
            return user_data

        client = self._create_app(get_user)
        resp = client.get("/secret")
        assert resp.status_code == 200
        assert "Hello bob" in resp.text

    def test_custom_redirect(self):
        async def no_user(request):
            return None

        app = FastAPI()
        ui = KokageUI(app)

        @ui.page("/secret")
        @protected(no_user, redirect_to="/signin")
        async def secret_page(request: Request):
            return Page(H1("Secret"))

        client = TestClient(app)
        resp = client.get("/secret", follow_redirects=False)
        assert resp.headers["location"] == "/signin"

    def test_role_check_passes(self):
        async def admin_user(request):
            return {"username": "alice", "role": "admin"}

        client = self._create_app(admin_user, role="admin")
        resp = client.get("/secret")
        assert resp.status_code == 200

    def test_role_check_fails(self):
        async def viewer_user(request):
            return {"username": "bob", "role": "viewer"}

        client = self._create_app(viewer_user, role="admin")
        resp = client.get("/secret")
        assert resp.status_code == 403

    def test_role_check_multiple_roles(self):
        async def editor_user(request):
            return {"username": "carol", "role": "editor"}

        client = self._create_app(editor_user, role=["admin", "editor"])
        resp = client.get("/secret")
        assert resp.status_code == 200

    def test_sync_auth_check(self):
        def sync_user(request):
            return {"username": "sync_user", "role": "admin"}

        client = self._create_app(sync_user)
        resp = client.get("/secret")
        assert resp.status_code == 200
        assert "Hello sync_user" in resp.text

    def test_cookie_based_auth(self):
        async def cookie_auth(request):
            token = request.cookies.get("session")
            if token == "valid":
                return {"username": "cookie_user", "role": "user"}
            return None

        client = self._create_app(cookie_auth)

        resp = client.get("/secret", follow_redirects=False)
        assert resp.status_code == 302

        resp = client.get("/secret", cookies={"session": "valid"})
        assert resp.status_code == 200
        assert "Hello cookie_user" in resp.text

    def test_user_roles_as_list(self):
        async def multi_role_user(request):
            return {"username": "admin", "role": ["viewer", "admin"]}

        client = self._create_app(multi_role_user, role="admin")
        resp = client.get("/secret")
        assert resp.status_code == 200
