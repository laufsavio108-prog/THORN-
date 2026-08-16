"""Contrato de Tool — a fronteira estável agente↔ferramenta.

Toda capacidade do THORN (ler /proc, rodar git, chamar cloud SDK) é uma Tool com
um `argv()` que descreve o que ela faria em termos de comando. O ToolRegistry
passa esse argv pela PermissionEngine ANTES de executar. O LLM pluga no mesmo
registry no MVP do agente — tool pedida pelo modelo passa pela mesma avaliação
que um comando humano.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str

    def argv(self, **kwargs: Any) -> list[str]:
        """Descreve a ação como um comando avaliável pela policy."""
        ...

    def run(self, **kwargs: Any) -> str:
        """Executa e devolve a saída. Só chamado se a policy autorizar."""
        ...
