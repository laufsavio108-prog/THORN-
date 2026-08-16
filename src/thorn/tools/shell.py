"""Execução segura de comando: subprocess com argv (lista), NUNCA shell=True.

Espelha a decisão do chronos: nada de string de shell — o argv já é o que a
PermissionEngine avaliou. Timeout e captura de stdout+stderr.
"""

from __future__ import annotations

import subprocess


def run_argv(argv: list[str], cwd: str | None = None, timeout: int = 30) -> str:
    try:
        proc = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        return f"[erro] binário não encontrado: {argv[0]}"
    except subprocess.TimeoutExpired:
        return f"[erro] timeout após {timeout}s"
    out = (proc.stdout or "") + (proc.stderr or "")
    return out.strip() or f"(sem saída, exit {proc.returncode})"
