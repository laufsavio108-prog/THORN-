"""Registry padrão do THORN com as tools embutidas já plugadas."""

from __future__ import annotations

from .builtins import GitStatusTool, ProcessesTool, SystemInfoTool
from .registry import ConfirmFn, ToolRegistry

_BUILTINS = (SystemInfoTool, ProcessesTool, GitStatusTool)


def build_registry(confirm: ConfirmFn | None = None) -> ToolRegistry:
    reg = ToolRegistry(confirm=confirm)
    for tool_cls in _BUILTINS:
        reg.register(tool_cls())
    return reg
