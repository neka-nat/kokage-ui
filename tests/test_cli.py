"""Tests for kokage CLI scaffolding tool."""

import os
import subprocess
import sys

import pytest

from kokage_ui.cli import _to_snake, cmd_add_crud, cmd_add_page, cmd_init


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
        args = _make_args(name="myapp", crud=False)
        cmd_init(args)

        assert (tmp_path / "myapp" / "app.py").exists()
        assert (tmp_path / "myapp" / "pyproject.toml").exists()

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "Welcome to myapp!" in app_content
        assert "KokageUI" in app_content

        pyproject_content = (tmp_path / "myapp" / "pyproject.toml").read_text()
        assert 'name = "myapp"' in pyproject_content
        assert '"kokage-ui"' in pyproject_content

        out = capsys.readouterr().out
        assert "Created myapp/" in out

    def test_creates_crud_project(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", crud=True)
        cmd_init(args)

        app_content = (tmp_path / "myapp" / "app.py").read_text()
        assert "InMemoryStorage" in app_content
        assert "ui.crud(" in app_content
        assert "class Item(BaseModel):" in app_content

    def test_existing_directory_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "myapp").mkdir()

        args = _make_args(name="myapp", crud=False)
        with pytest.raises(SystemExit, match="1"):
            cmd_init(args)

        err = capsys.readouterr().err
        assert "already exists" in err

    def test_output_shows_run_instructions(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = _make_args(name="myapp", crud=False)
        cmd_init(args)

        out = capsys.readouterr().out
        assert "cd myapp" in out
        assert "uv sync" in out


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


# --- main() via argparse ---


class TestMain:
    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "kokage" in result.stdout

    def test_init_subcommand(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.cli", "init", "testproject"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert (tmp_path / "testproject" / "app.py").exists()

    def test_no_args_shows_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "kokage_ui.cli"],
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
