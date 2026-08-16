"""Tools embutidas do THORN (0.2) — determinísticas, rodam sem IA nem key.

Todas passam pela PermissionEngine via ToolRegistry. As três primeiras são
somente-leitura (SAFE): descrevem o host, os processos e o estado de um repo git.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any

from .shell import run_argv


class SystemInfoTool:
    name = "system_info"
    description = "SO, kernel, arquitetura, CPUs e loadavg do host."

    def argv(self, **_: Any) -> list[str]:
        return ["system", "info"]  # SAFE: descritivo, não executa nada externo

    def run(self, **_: Any) -> str:
        u = platform.uname()
        lines = [
            f"host   : {u.node}",
            f"os     : {u.system} {u.release}",
            f"arch   : {u.machine}",
            f"python : {platform.python_version()}",
            f"cpus   : {os.cpu_count()}",
        ]
        try:
            la = os.getloadavg()
            lines.append(f"load   : {la[0]:.2f} {la[1]:.2f} {la[2]:.2f}")
        except (OSError, AttributeError):
            lines.append("load   : n/a (indisponível no Windows)")
        return "\n".join(lines)


class ProcessesTool:
    name = "system_processes"
    description = "Top processos por memória residente (lê /proc, só Linux)."

    def argv(self, **_: Any) -> list[str]:
        return ["ps"]  # SAFE

    def run(self, limit: int = 10, **_: Any) -> str:
        proc = Path("/proc")
        if not proc.exists():
            return "system_processes: disponível só em Linux (sem /proc neste host)."
        page = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096
        rows: list[tuple[int, int, str]] = []
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                # statm: campo 2 = RSS em páginas
                rss_pages = int((entry / "statm").read_text().split()[1])
                comm = (entry / "comm").read_text().strip()
            except (OSError, IndexError, ValueError):
                continue
            rows.append((rss_pages * page, int(entry.name), comm))
        rows.sort(reverse=True)
        out = [f"{'PID':>7}  {'RSS(MB)':>8}  COMANDO"]
        for rss, pid, comm in rows[:limit]:
            out.append(f"{pid:>7}  {rss / 1_048_576:>8.1f}  {comm}")
        return "\n".join(out)


class GitStatusTool:
    name = "git_status"
    description = "git status --short --branch de um repositório (path)."

    def argv(self, path: str = ".", **_: Any) -> list[str]:
        return ["git", "status"]  # SAFE: leitura

    def run(self, path: str = ".", **_: Any) -> str:
        return run_argv(["git", "-C", path, "status", "--short", "--branch"])
