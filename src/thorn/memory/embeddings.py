"""Embeddings plugáveis.

O 0.1 usa um embedder determinístico, offline e sem dependências (HashingEmbedder):
suficiente para provar "incidente similar" sem key nem download de modelo. Troque
por um modelo local (sentence-transformers) ou Voyage quando quiser qualidade —
basta implementar `Embedder.embed` e registrar em `get_embedder`.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol


class Embedder(Protocol):
    dim: int

    def embed(self, text: str) -> list[float]: ...


_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _stable_bucket(token: str, dim: int) -> int:
    """Hash ESTÁVEL entre processos (o hash() embutido do Python é randomizado
    por PYTHONHASHSEED, o que quebraria embeddings gravados e relidos depois)."""
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dim


class HashingEmbedder:
    """Bag-of-words + bigramas hasheados em `dim` buckets, L2-normalizado.

    Determinístico (mesmo texto → mesmo vetor), então dá para versionar testes.
    Não captura sinônimos como um modelo neural, mas agrupa incidentes que
    compartilham vocabulário — o bastante para o loop de investigação do 0.1.
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        toks = _tokens(text)
        grams = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        for g in grams:
            vec[_stable_bucket(g, self.dim)] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosseno de dois vetores já L2-normalizados (= produto interno)."""
    return sum(x * y for x, y in zip(a, b))


def get_embedder(name: str = "hashing") -> Embedder:
    if name == "hashing":
        return HashingEmbedder()
    raise ValueError(f"embedder desconhecido: {name!r} (disponível: hashing)")
