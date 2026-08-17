"""Engine do catálogo: índice por categoria, detalhe e busca.

Busca tolerante a acento e caixa (memoria → memória) via normalização NFD,
igual ao catálogo do chronos. Procura em nome, descrição e exemplos.
"""

from __future__ import annotations

import unicodedata

from .data import COMMANDS, Command


def _norm(s: str) -> str:
    """minúsculas + sem acento (NFD, remove diacríticos)."""
    nfd = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def all_commands() -> list[Command]:
    return COMMANDS


def get(name: str) -> Command | None:
    """Detalhe por nome exato (tolerante a acento/caixa/espaços)."""
    key = _norm(name).strip()
    for c in COMMANDS:
        if _norm(c.name) == key:
            return c
    return None


def by_category(tool: str | None = None) -> dict[str, list[Command]]:
    """Comandos agrupados por categoria, opcionalmente filtrando linux/git."""
    groups: dict[str, list[Command]] = {}
    for c in COMMANDS:
        if tool and c.tool != tool:
            continue
        groups.setdefault(f"{c.tool} · {c.cat}", []).append(c)
    return groups


def search(query: str) -> list[Command]:
    """Busca em nome, descrição e exemplos. Nome que casa vem primeiro."""
    q = _norm(query)
    hits: list[tuple[int, Command]] = []
    for c in COMMANDS:
        blob = _norm(" ".join([c.name, c.desc, c.usage, *c.examples]))
        if q not in blob:
            continue
        rank = 0 if q in _norm(c.name) else 1  # match no nome ranqueia acima
        hits.append((rank, c))
    hits.sort(key=lambda t: (t[0], t[1].name))
    return [c for _, c in hits]
