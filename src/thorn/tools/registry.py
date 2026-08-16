"""ToolRegistry — valida risco → confirma → executa.

Ponto único por onde passa toda execução de tool, seja pedida por humano ou pelo
LLM. Um `confirm` injetável decide o que fazer no caso CONFIRM (na CLI, pergunta;
no modo autônomo, nega por padrão).
"""

from __future__ import annotations

from typing import Any, Callable

from ..security.policy import PermissionEngine, Risk
from .base import Tool

ConfirmFn = Callable[[str, list[str]], bool]


def _deny_by_default(reason: str, argv: list[str]) -> bool:
    return False


class ToolDenied(Exception):
    pass


class ToolRegistry:
    def __init__(self, confirm: ConfirmFn | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        self._policy = PermissionEngine()
        self._confirm = confirm or _deny_by_default

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def describe(self, name: str) -> str:
        tool = self._tools.get(name)
        return tool.description if tool else ""

    def invoke(self, name: str, **kwargs: Any) -> str:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolDenied(f"tool desconhecida: {name!r}")

        argv = tool.argv(**kwargs)
        decision = self._policy.assess(argv)

        if decision.risk is Risk.BLOCKED:
            raise ToolDenied(
                f"BLOCKED ({decision.reason}). Rode você mesmo, se for o caso:\n  {' '.join(argv)}"
            )
        if decision.risk is Risk.CONFIRM and not self._confirm(decision.reason, argv):
            raise ToolDenied(f"não confirmado ({decision.reason})")

        return tool.run(**kwargs)
