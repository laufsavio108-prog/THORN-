"""Testes do catálogo Linux + Git."""

from __future__ import annotations

from thorn import reference


def test_tem_linux_git_docker() -> None:
    tools = {c.tool for c in reference.all_commands()}
    assert tools == {"linux", "git", "docker"}


def test_get_por_nome_exato() -> None:
    c = reference.get("git status")
    assert c is not None and c.tool == "git"


def test_get_tolerante_a_acento_e_caixa() -> None:
    # busca por "git status" com caixa alta deve achar
    assert reference.get("GIT STATUS") is not None


def test_busca_acha_por_descricao() -> None:
    # "dns" está na descrição/exemplos do dig
    hits = reference.search("dns")
    assert any(c.name == "dig" for c in hits)


def test_busca_tolerante_a_acento() -> None:
    # "historico" (sem acento) deve achar comandos da categoria "histórico"
    hits = reference.search("historico")
    assert any(c.name == "git log" for c in hits)


def test_busca_nome_ranqueia_acima() -> None:
    # buscar "grep" deve trazer o próprio grep em primeiro
    hits = reference.search("grep")
    assert hits and hits[0].name == "grep"


def test_por_categoria_filtra_por_tool() -> None:
    grupos = reference.by_category("git")
    assert grupos and all("git" in cat for cat in grupos)
