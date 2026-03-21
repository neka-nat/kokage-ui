"""Tests for ToolRegistry."""

import pytest

from kokage_ui.ai.tools import ToolInfo, ToolRegistry, _build_json_schema


class TestBuildJsonSchema:
    def test_basic_types(self):
        def fn(name: str, age: int, score: float, active: bool) -> str: ...

        schema = _build_json_schema(fn)
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "integer"}
        assert schema["properties"]["score"] == {"type": "number"}
        assert schema["properties"]["active"] == {"type": "boolean"}
        assert set(schema["required"]) == {"name", "age", "score", "active"}

    def test_default_values(self):
        def fn(query: str, limit: int = 10) -> str: ...

        schema = _build_json_schema(fn)
        assert schema["required"] == ["query"]
        assert schema["properties"]["limit"] == {"type": "integer", "default": 10}

    def test_list_type(self):
        def fn(items: list[str]) -> str: ...

        schema = _build_json_schema(fn)
        assert schema["properties"]["items"] == {"type": "array", "items": {"type": "string"}}

    def test_dict_type(self):
        def fn(data: dict) -> str: ...

        schema = _build_json_schema(fn)
        assert schema["properties"]["data"] == {"type": "object"}

    def test_no_hints_defaults_to_string(self):
        def fn(x) -> str: ...

        schema = _build_json_schema(fn)
        assert schema["properties"]["x"] == {"type": "string"}

    def test_skips_self(self):
        def fn(self, query: str) -> str: ...

        schema = _build_json_schema(fn)
        assert "self" not in schema["properties"]


class TestToolRegistry:
    def test_decorator_no_args(self):
        reg = ToolRegistry()

        @reg.tool
        def search(query: str) -> str:
            """Search the database."""
            return query

        assert "search" in reg
        assert len(reg) == 1
        info = reg.get("search")
        assert info.name == "search"
        assert info.description == "Search the database."

    def test_decorator_with_args(self):
        reg = ToolRegistry()

        @reg.tool(name="my_search", description="Custom search tool")
        def search(query: str) -> str:
            return query

        assert "my_search" in reg
        info = reg.get("my_search")
        assert info.description == "Custom search tool"

    def test_list_and_names(self):
        reg = ToolRegistry()

        @reg.tool
        def a() -> str: ...

        @reg.tool
        def b() -> str: ...

        assert reg.names() == ["a", "b"]
        assert len(reg.list()) == 2

    def test_async_tool(self):
        reg = ToolRegistry()

        @reg.tool
        async def fetch(url: str) -> str:
            """Fetch a URL."""
            return url

        info = reg.get("fetch")
        assert info.is_async

    def test_sync_tool(self):
        reg = ToolRegistry()

        @reg.tool
        def calc(expr: str) -> str:
            return expr

        info = reg.get("calc")
        assert not info.is_async

    def test_schema_generation(self):
        reg = ToolRegistry()

        @reg.tool
        def greet(name: str, times: int = 1) -> str:
            """Say hello."""
            return f"Hello {name}" * times

        info = reg.get("greet")
        assert info.parameters["properties"]["name"]["type"] == "string"
        assert info.parameters["properties"]["times"]["default"] == 1
        assert info.parameters["required"] == ["name"]

    def test_get_missing(self):
        reg = ToolRegistry()
        assert reg.get("nonexistent") is None

    def test_contains(self):
        reg = ToolRegistry()

        @reg.tool
        def x() -> str: ...

        assert "x" in reg
        assert "y" not in reg

    def test_original_function_preserved(self):
        reg = ToolRegistry()

        @reg.tool
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5

    @pytest.mark.asyncio
    async def test_ainvoke_sync(self):
        reg = ToolRegistry()

        @reg.tool
        def double(n: int) -> int:
            return n * 2

        info = reg.get("double")
        result = await info.ainvoke(n=5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_ainvoke_async(self):
        reg = ToolRegistry()

        @reg.tool
        async def double(n: int) -> int:
            return n * 2

        info = reg.get("double")
        result = await info.ainvoke(n=5)
        assert result == 10

    def test_no_docstring_uses_name(self):
        reg = ToolRegistry()

        @reg.tool
        def mystery(x: str) -> str:
            return x

        info = reg.get("mystery")
        assert info.description == "mystery"
