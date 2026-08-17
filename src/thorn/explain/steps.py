"""Passo anotado de um 'explain' — uma camada da pilha, com dado real + explicação."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Step:
    layer: str            # DNS | TCP | TLS | HTTP | IP | ICMP | INFO
    title: str            # manchete com o dado REAL da conexão
    explain: str          # o que essa camada faz, em PT-BR
    detail: list[str] = field(default_factory=list)  # linhas de dado real extra
    ok: bool = True


# cor por camada (Rich)
LAYER_STYLE = {
    "DNS": "magenta",
    "TCP": "cyan",
    "TLS": "green",
    "HTTP": "yellow",
    "IP": "blue",
    "ICMP": "cyan",
    "INFO": "grey70",
}
