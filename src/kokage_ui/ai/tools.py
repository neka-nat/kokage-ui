"""Tool registry for AI agent integration.

Provides a decorator-based registry for defining tools that can be used
with kokage-ui's AgentView and converted to LangChain tools.

Example::

    from kokage_ui.ai.tools import ToolRegistry

    registry = ToolRegistry()

    @registry.tool
    async def search(query: str, limit: int = 5) -> str:
        \"\"\"Search the database for matching records.\"\"\"
        return f"Found results for: {query}"

    @registry.tool(name="calculate", description="Evaluate a math expression")
    def calc(expression: str) -> str:
        return str(eval(expression))

    # List registered tools
    for info in registry.list():
        print(info.name, info.description, info.parameters)
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from pydantic import BaseModel


class ToolInfo(BaseModel):
    """Metadata for a registered tool.

    Args:
        name: Tool name.
        description: Tool description (from docstring or override).
        parameters: JSON Schema for the tool's input parameters.
        func: The original callable (excluded from serialization).
    """

    name: str
    description: str
    parameters: dict[str, Any]
    func: Any = None

    model_config = {"arbitrary_types_allowed": True}

    @property
    def is_async(self) -> bool:
        return asyncio.iscoroutinefunction(self.func)

    async def ainvoke(self, **kwargs: Any) -> Any:
        """Call the tool, awaiting if async."""
        if self.is_async:
            return await self.func(**kwargs)
        return self.func(**kwargs)


def _build_json_schema(func: Callable) -> dict[str, Any]:
    """Build a JSON Schema object from function type hints."""
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []

    type_map: dict[type, str] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        dict: "object",
        list: "array",
    }

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        hint = hints.get(param_name, str)
        origin = getattr(hint, "__origin__", None)

        if origin is list:
            prop: dict[str, Any] = {"type": "array"}
            args = getattr(hint, "__args__", ())
            if args:
                item_type = type_map.get(args[0], "string")
                prop["items"] = {"type": item_type}
        elif origin is dict:
            prop = {"type": "object"}
        else:
            prop = {"type": type_map.get(hint, "string")}

        if param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            required.append(param_name)

        properties[param_name] = prop

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


class ToolRegistry:
    """Registry for AI agent tools.

    Tools are registered via the :meth:`tool` decorator and can be
    listed, looked up, or converted to LangChain format.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolInfo] = {}

    def tool(
        self,
        func: Callable | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Any:
        """Register a tool function.

        Can be used as ``@registry.tool`` or ``@registry.tool(name=..., description=...)``.
        """
        def decorator(fn: Callable) -> Callable:
            tool_name = name or fn.__name__
            tool_desc = description or (inspect.getdoc(fn) or "").strip() or tool_name
            schema = _build_json_schema(fn)
            info = ToolInfo(name=tool_name, description=tool_desc, parameters=schema, func=fn)
            self._tools[tool_name] = info
            return fn

        if func is not None:
            return decorator(func)
        return decorator

    def get(self, name: str) -> ToolInfo | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list(self) -> list[ToolInfo]:
        """List all registered tools."""
        return list(self._tools.values())

    def names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
