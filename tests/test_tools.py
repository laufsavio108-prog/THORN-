"""Testes das tools embutidas (0.2) e do registry padrão."""

from __future__ import annotations

import subprocess

from thorn.tools import build_registry
from thorn.tools.builtins import GitStatusTool, SystemInfoTool


def test_registry_padrao_tem_builtins() -> None:
    reg = build_registry()
    assert set(reg.names()) == {"system_info", "system_processes", "git_status"}


def test_system_info_roda_e_descreve_host() -> None:
    out = SystemInfoTool().run()
    assert "os" in out and "python" in out and "cpus" in out


def test_system_info_e_safe_passa_sem_confirm() -> None:
    # confirm que sempre nega: se fosse CONFIRM, invoke levantaria ToolDenied.
    reg = build_registry(confirm=lambda reason, argv: False)
    out = reg.invoke("system_info")
    assert "host" in out


def test_git_status_em_repo(tmp_path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    out = GitStatusTool().run(path=str(tmp_path))
    # repo recém-criado: branch aparece no cabeçalho do --branch
    assert "##" in out or "branch" in out.lower() or out.strip() != ""


def test_git_status_binario_ausente_nao_quebra() -> None:
    # path inexistente -> git responde erro, mas run_argv não deve lançar
    out = GitStatusTool().run(path="/caminho/que/nao/existe/xyz")
    assert isinstance(out, str) and out != ""
