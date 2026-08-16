"""Permission engine — portado do chronos (TS).

Filosofia do THORN: o agente RECOMENDA, você EXECUTA. A avaliação é por
ARGUMENTO, não por binário: `git status` é SAFE, `git push` é CONFIRM, `rm -rf /`
é BLOCKED — mesmo o binário sendo o mesmo em muitos casos.

Risk:
    SAFE     -> roda direto.
    CONFIRM  -> pede confirmação humana antes de executar.
    BLOCKED  -> nunca roda; o THORN só mostra o comando pra você rodar à mão.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Risk(enum.IntEnum):
    SAFE = 0
    CONFIRM = 1
    BLOCKED = 2


@dataclass(frozen=True)
class Decision:
    risk: Risk
    reason: str

    @property
    def allowed_without_confirm(self) -> bool:
        return self.risk is Risk.SAFE


# Padrões de argumento que elevam o risco. Ordem importa: o primeiro match vence.
_BLOCKED = (
    ("rm", "-rf", "/"),
    ("mkfs",),
    ("dd", "of=/dev"),
    (":(){", ),  # fork bomb
)
_CONFIRM_TOKENS = {
    "push", "commit", "rm", "mv", "chmod", "chown", "kill", "reboot", "shutdown",
    "systemctl", "restart", "stop", "install", "apt", "pip", "drop", "delete",
}


class PermissionEngine:
    def assess(self, argv: list[str]) -> Decision:
        flat = [a.lower() for a in argv]
        joined = " ".join(flat)

        for pattern in _BLOCKED:
            if all(tok in joined for tok in pattern):
                return Decision(Risk.BLOCKED, f"padrão destrutivo: {' '.join(pattern)}")

        for tok in flat:
            if tok in _CONFIRM_TOKENS:
                return Decision(Risk.CONFIRM, f"ação sensível: {tok}")

        return Decision(Risk.SAFE, "somente leitura / inofensivo")
