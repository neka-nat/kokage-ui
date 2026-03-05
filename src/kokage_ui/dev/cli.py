"""kokage CLI — Project scaffolding tool."""

import argparse
import os
import sys

from kokage_ui.dev.templates import (
    APP_CRUD_TEMPLATE,
    APP_TEMPLATE,
    CRUD_MODEL_TEMPLATE,
    PAGE_TEMPLATE,
    PYPROJECT_TEMPLATE,
)


def _write_file(path: str, content: str) -> None:
    """Write content to file, creating parent directories."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  {path}")


def cmd_init(args: argparse.Namespace) -> None:
    name = args.name
    base = name

    if os.path.exists(base):
        print(f"Error: '{base}' already exists.", file=sys.stderr)
        sys.exit(1)

    print(f"Created {base}/")

    if args.crud:
        _write_file(f"{base}/app.py", APP_CRUD_TEMPLATE.format(name=name))
    else:
        _write_file(f"{base}/app.py", APP_TEMPLATE.format(name=name))

    _write_file(f"{base}/pyproject.toml", PYPROJECT_TEMPLATE.format(name=name))

    print(f"\nRun:\n  cd {name}\n  uv sync\n  uv run uvicorn app:app --reload")


def cmd_add_page(args: argparse.Namespace) -> None:
    name = args.name
    title = name.replace("_", " ").replace("-", " ").title()
    path = f"pages/{name}.py"

    if os.path.exists(path):
        print(f"Error: '{path}' already exists.", file=sys.stderr)
        sys.exit(1)

    _write_file(path, PAGE_TEMPLATE.format(name=name, title=title))
    print(f"\nAdd to your app.py:")
    print(f"  from pages.{name} import register")
    print(f"  register(ui)")


def cmd_add_crud(args: argparse.Namespace) -> None:
    model_name = args.name
    snake = _to_snake(model_name)
    path = f"models/{snake}.py"

    if os.path.exists(path):
        print(f"Error: '{path}' already exists.", file=sys.stderr)
        sys.exit(1)

    _write_file(path, CRUD_MODEL_TEMPLATE.format(model=model_name, snake=snake))
    plural = snake + "s"
    print(f"\nAdd to your app.py:")
    print(f"  from models.{snake} import {model_name}, {snake}_storage")
    print(f'  ui.crud("/{plural}", model={model_name}, storage={snake}_storage, title="{model_name}s")')


def _to_snake(name: str) -> str:
    """CamelCase to snake_case."""
    result = []
    for i, c in enumerate(name):
        if c.isupper() and i > 0:
            result.append("_")
        result.append(c.lower())
    return "".join(result)


def main() -> None:
    parser = argparse.ArgumentParser(prog="kokage-ui", description="kokage-ui scaffolding tool")
    sub = parser.add_subparsers(dest="command")

    # kokage init
    init_p = sub.add_parser("init", help="Create a new project")
    init_p.add_argument("name", help="Project name")
    init_p.add_argument("--crud", action="store_true", help="Include CRUD template")

    # kokage add
    add_p = sub.add_parser("add", help="Add page or CRUD model")
    add_sub = add_p.add_subparsers(dest="add_type")

    page_p = add_sub.add_parser("page", help="Add a new page")
    page_p.add_argument("name", help="Page name (e.g. dashboard)")

    crud_p = add_sub.add_parser("crud", help="Add a CRUD model")
    crud_p.add_argument("name", help="Model name in CamelCase (e.g. Product)")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "add":
        if args.add_type == "page":
            cmd_add_page(args)
        elif args.add_type == "crud":
            cmd_add_crud(args)
        else:
            add_p.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
