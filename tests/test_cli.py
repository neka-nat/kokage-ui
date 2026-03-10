"""Tests for kokage CLI scaffolding tool."""

import os
import subprocess
import sys

import pytest

from kokage_ui.dev.cli import _to_snake, cmd_add_crud, cmd_add_page, cmd_init, cmd_templates
from kokage_ui.dev.templates import TEMPLATES


# --- _to_snake ---


class TestToSnake:
    def test_simple(self):
        assert _to_snake("Product") == "product"

    def test_two_words(self):
        assert _to_snake("MyModel") == "my_model"

    def test_three_words(self):
        assert _to_snake("MyBigModel") == "my_big_model"

    def test_single_lower(self):
        assert _to_snake("item") == "item"

    def test_all_caps(self):
        assert _to_snake("API") == "a_p_i"

    def test_single_char(self):
        assert _to_snake("X") == "x"


# --- cmd_init ---


class TestCmdInit:
    def test_creates_project(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template=None)
        cmd_init(args)

        assert (tmp_path / "myapp" / "app.py").exists()
        assert (tmp_path / "myapp" / "pyproject.toml").exists()
        assert (tmp_path / "myapp" / ".gitignore").exists()
        assert (tmp_path / "myapp" / "README.md").exists()

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "Welcome to myapp!" in app_content
        assert "KokageUI" in app_content

        pyproject_content = (tmp_path / "myapp" / "pyproject.toml").read_text()
        assert 'name = "myapp"' in pyproject_content
        assert '"kokage-ui"' in pyproject_content

        readme_content = (tmp_path / "myapp" / "README.md").read_text()
        assert "# myapp" in readme_content

        out = capsys.readouterr().out
        assert "Created myapp/" in out
        assert "template: basic" in out

    def test_creates_crud_project(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template="crud")
        cmd_init(args)

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "InMemoryStorage" in app_content
        assert "ui.crud(" in app_content
        assert "class Item(BaseModel):" in app_content

    def test_existing_directory_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "myapp").mkdir()

        args = _make_args(name="myapp", template=None)
        with pytest.raises(SystemExit, match="1"):
            cmd_init(args)

        err = capsys.readouterr().err
        assert "already exists" in err

    def test_output_shows_run_instructions(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template=None)
        cmd_init(args)

        out = capsys.readouterr().out
        assert "cd myapp" in out
        assert "uv sync" in out


class TestCmdInitTemplates:
    """Test --template option for each template type."""

    def test_unknown_template_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template="nonexistent")
        with pytest.raises(SystemExit, match="1"):
            cmd_init(args)

        err = capsys.readouterr().err
        assert "Unknown template" in err

    def test_admin_template(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template="admin")
        cmd_init(args)

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "AdminSite" in app_content
        assert "SQLModelStorage" in app_content
        assert "create_async_engine" in app_content

        pyproject_content = (tmp_path / "myapp" / "pyproject.toml").read_text()
        assert '"kokage-ui[sql]"' in pyproject_content

    def test_dashboard_template(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template="dashboard")
        cmd_init(args)

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "Chart" in app_content
        assert "Stats" in app_content
        assert "Stat" in app_content

    def test_chat_template(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template="chat")
        cmd_init(args)

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "ChatView" in app_content
        assert "chat_stream" in app_content

    def test_agent_template(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template="agent")
        cmd_init(args)

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "AgentView" in app_content
        assert "agent_stream" in app_content
        assert "AgentEvent" in app_content

    def test_all_templates_generate_valid_python(self, tmp_path, monkeypatch, capsys):
        """Every template should produce syntactically valid Python."""
        for key in TEMPLATES:
            project_dir = tmp_path / f"proj_{key}"
            monkeypatch.chdir(tmp_path)
            args = _make_args(name=f"proj_{key}", template=key)
            cmd_init(args)

            app_file = project_dir / "app.py"
            assert app_file.exists(), f"app.py not created for template '{key}'"

            # Check syntax by compiling
            source = app_file.read_text()
            compile(source, str(app_file), "exec")

    def test_gitignore_created(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template=None)
        cmd_init(args)

        gitignore = (tmp_path / "myapp" / ".gitignore").read_text()
        assert "__pycache__/" in gitignore
        assert "*.db" in gitignore

    def test_readme_created(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", template=None)
        cmd_init(args)

        readme = (tmp_path / "myapp" / "README.md").read_text()
        assert "# myapp" in readme
        assert "uvicorn app:app" in readme


# --- cmd_add_page ---


class TestCmdAddPage:
    def test_creates_page(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="dashboard")
        cmd_add_page(args)

        path = tmp_path / "pages" / "dashboard.py"
        assert path.exists()

        content = path.read_text()
        assert "def register(ui: KokageUI)" in content
        assert 'H1("Dashboard"' in content
        assert '"/dashboard"' in content

        out = capsys.readouterr().out
        assert "from pages.dashboard import register" in out

    def test_underscore_name(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="user_settings")
        cmd_add_page(args)

        content = (tmp_path / "pages" / "user_settings.py").read_text()
        assert 'H1("User Settings"' in content

    def test_existing_file_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pages").mkdir()
        (tmp_path / "pages" / "dashboard.py").write_text("existing")

        args = _make_args(name="dashboard")
        with pytest.raises(SystemExit, match="1"):
            cmd_add_page(args)

        err = capsys.readouterr().err
        assert "already exists" in err


# --- cmd_add_crud ---


class TestCmdAddCrud:
    def test_creates_model(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="Product")
        cmd_add_crud(args)

        path = tmp_path / "models" / "product.py"
        assert path.exists()

        content = path.read_text()
        assert "class Product(BaseModel):" in content
        assert "product_storage = InMemoryStorage(Product)" in content

        out = capsys.readouterr().out
        assert "from models.product import Product, product_storage" in out
        assert '"/products"' in out

    def test_camel_case_conversion(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="BlogPost")
        cmd_add_crud(args)

        path = tmp_path / "models" / "blog_post.py"
        assert path.exists()

        content = path.read_text()
        assert "class BlogPost(BaseModel):" in content
        assert "blog_post_storage = InMemoryStorage(BlogPost)" in content

        out = capsys.readouterr().out
        assert '"/blog_posts"' in out

    def test_existing_file_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "models").mkdir()
        (tmp_path / "models" / "product.py").write_text("existing")

        args = _make_args(name="Product")
        with pytest.raises(SystemExit, match="1"):
            cmd_add_crud(args)

        err = capsys.readouterr().err
        assert "already exists" in err


# --- cmd_templates ---


class TestCmdTemplates:
    def test_lists_all_templates(self, capsys):
        cmd_templates(_make_args())

        out = capsys.readouterr().out
        for key in TEMPLATES:
            assert key in out

    def test_shows_descriptions(self, capsys):
        cmd_templates(_make_args())

        out = capsys.readouterr().out
        for _key, (desc, _tmpl, _sql) in TEMPLATES.items():
            assert desc in out


# --- main() via argparse ---


class TestMain:
    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.dev.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "kokage" in result.stdout

    def test_init_subcommand(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.dev.cli", "init", "testproject"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert (tmp_path / "testproject" / "app.py").exists()

    def test_init_with_template_flag(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.dev.cli", "init", "testproject", "--template", "dashboard"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        app_content = (tmp_path / "testproject" / "app.py").read_text()
        assert "Chart" in app_content

    def test_init_with_short_template_flag(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.dev.cli", "init", "testproject", "-t", "chat"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        app_content = (tmp_path / "testproject" / "app.py").read_text()
        assert "ChatView" in app_content

    def test_templates_subcommand(self):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.dev.cli", "templates"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "basic" in result.stdout
        assert "admin" in result.stdout

    def test_no_args_shows_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.dev.cli"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower() or "kokage" in result.stdout


# --- helpers ---


def _make_args(**kwargs):
    """Create a simple namespace to simulate argparse args."""
    from argparse import Namespace

    return Namespace(**kwargs)
