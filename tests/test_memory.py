"""Testes do MemoryStore — com foco no diferencial: isolamento por ambiente."""

from __future__ import annotations

from pathlib import Path

import pytest

from thorn.memory import MemoryStore
from thorn.security import PermissionEngine, Risk
from thorn.tools import ToolDenied, ToolRegistry


@pytest.fixture()
def store(tmp_path: Path) -> MemoryStore:
    s = MemoryStore(tmp_path / "t.db")
    yield s
    s.close()


def test_cria_e_lista_ambientes(store: MemoryStore) -> None:
    store.create_environment("empresa-a", "company")
    store.create_environment("lab-pessoal", "personal")
    nomes = [e.name for e in store.list_environments()]
    assert nomes == ["empresa-a", "lab-pessoal"]


def test_incidente_similar_encontra_por_vocabulario(store: MemoryStore) -> None:
    env = store.create_environment("empresa-a", "company")
    store.add_incident(env.id, "Usuário sem acesso ao ERP", "erp.company.local retorna NXDOMAIN, falha de DNS")
    store.add_incident(env.id, "Impressora offline", "spooler travado no windows")

    hits = store.similar_incidents(env.id, "não resolve DNS do ERP interno")
    assert hits, "deveria achar ao menos um incidente"
    assert "ERP" in hits[0].incident.title  # o de DNS vem primeiro


def test_ISOLAMENTO_entre_ambientes(store: MemoryStore) -> None:
    """A invariante que carrega a visão: Empresa A nunca vê Empresa B."""
    a = store.create_environment("empresa-a", "company")
    b = store.create_environment("empresa-b", "company")
    store.add_incident(a.id, "VPN caindo", "túnel ipsec derruba a cada 30min")

    # Buscando no ambiente B pelo MESMO texto: não pode achar nada da Empresa A.
    hits_b = store.similar_incidents(b.id, "vpn ipsec caindo")
    assert hits_b == []

    hits_a = store.similar_incidents(a.id, "vpn ipsec caindo")
    assert len(hits_a) == 1


def test_memoria_tambem_isola(store: MemoryStore) -> None:
    a = store.create_environment("empresa-a", "company")
    b = store.create_environment("lab-pessoal", "personal")
    store.add_memory(a.id, "credencial do firewall expira a cada 90 dias")
    assert store.search_memory(b.id, "credencial firewall") == []
    assert store.search_memory(a.id, "credencial firewall")


# --- fronteira Tool/Permissão ------------------------------------------------


def test_policy_por_argumento() -> None:
    p = PermissionEngine()
    assert p.assess(["git", "status"]).risk is Risk.SAFE
    assert p.assess(["git", "push"]).risk is Risk.CONFIRM
    assert p.assess(["rm", "-rf", "/"]).risk is Risk.BLOCKED


class _EchoTool:
    name = "echo"
    description = "ecoa argumentos"

    def __init__(self, argv: list[str]) -> None:
        self._argv = argv

    def argv(self, **_: object) -> list[str]:
        return self._argv

    def run(self, **_: object) -> str:
        return "ran"


def test_registry_bloqueia_e_confirma() -> None:
    reg = ToolRegistry(confirm=lambda reason, argv: False)  # nega CONFIRM por padrão
    reg.register(_EchoTool(["git", "status"]))
    assert reg.invoke("echo") == "ran"

    reg2 = ToolRegistry(confirm=lambda reason, argv: False)
    reg2.register(_EchoTool(["git", "push"]))
    with pytest.raises(ToolDenied):
        reg2.invoke("echo")
