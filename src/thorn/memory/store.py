"""MemoryStore — a peça que carrega a visão do THORN.

Todo método de leitura de incidents/memories recebe (e filtra por) environment_id.
Esse é o contrato que garante o isolamento entre ambientes. A busca de "incidente
similar" ranqueia por cosseno de embeddings, sempre dentro do ambiente.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .db import connect
from .embeddings import Embedder, cosine, get_embedder


@dataclass(frozen=True)
class Environment:
    id: int
    name: str
    kind: str
    description: str


@dataclass(frozen=True)
class Incident:
    id: int
    environment_id: int
    title: str
    problem: str
    status: str
    root_cause: str | None
    resolution: str | None


@dataclass(frozen=True)
class SimilarIncident:
    incident: Incident
    score: float


class MemoryStore:
    def __init__(self, db_path: Path, embedder: Embedder | None = None) -> None:
        self._conn = connect(db_path)
        self._embedder = embedder or get_embedder()

    def close(self) -> None:
        self._conn.close()

    # --- ambientes -------------------------------------------------------

    def create_environment(self, name: str, kind: str = "personal", description: str = "") -> Environment:
        cur = self._conn.execute(
            "INSERT INTO environments(name, kind, description) VALUES (?, ?, ?)",
            (name, kind, description),
        )
        self._conn.commit()
        return Environment(cur.lastrowid, name, kind, description)

    def get_environment(self, name: str) -> Environment | None:
        row = self._conn.execute(
            "SELECT id, name, kind, description FROM environments WHERE name = ?", (name,)
        ).fetchone()
        return _env(row) if row else None

    def list_environments(self) -> list[Environment]:
        rows = self._conn.execute(
            "SELECT id, name, kind, description FROM environments ORDER BY name"
        ).fetchall()
        return [_env(r) for r in rows]

    # --- incidentes ------------------------------------------------------

    def add_incident(self, env_id: int, title: str, problem: str) -> Incident:
        emb = self._embedder.embed(f"{title}\n{problem}")
        cur = self._conn.execute(
            "INSERT INTO incidents(environment_id, title, problem, embedding) VALUES (?, ?, ?, ?)",
            (env_id, title, problem, json.dumps(emb)),
        )
        self._conn.commit()
        self._audit(env_id, "incident:add", title)
        return Incident(cur.lastrowid, env_id, title, problem, "open", None, None)

    def resolve_incident(self, incident_id: int, root_cause: str, resolution: str) -> None:
        self._conn.execute(
            "UPDATE incidents SET status='resolved', root_cause=?, resolution=?, "
            "resolved_at=datetime('now') WHERE id=?",
            (root_cause, resolution, incident_id),
        )
        self._conn.commit()

    def similar_incidents(self, env_id: int, query: str, k: int = 5) -> list[SimilarIncident]:
        """Incidentes do MESMO ambiente mais parecidos com `query`, por cosseno.

        O filtro `WHERE environment_id = ?` é o coração do isolamento: a busca
        nunca vê incidentes de outro ambiente.
        """
        q = self._embedder.embed(query)
        rows = self._conn.execute(
            "SELECT id, environment_id, title, problem, status, root_cause, resolution, embedding "
            "FROM incidents WHERE environment_id = ?",
            (env_id,),
        ).fetchall()
        scored = [
            SimilarIncident(_incident(r), cosine(q, json.loads(r["embedding"])))
            for r in rows
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        return [s for s in scored if s.score > 0.0][:k]

    # --- memórias --------------------------------------------------------

    def add_memory(self, env_id: int, content: str, kind: str = "technical", source: str = "user") -> int:
        emb = self._embedder.embed(content)
        cur = self._conn.execute(
            "INSERT INTO memories(environment_id, kind, content, source, embedding) VALUES (?, ?, ?, ?, ?)",
            (env_id, kind, content, source, json.dumps(emb)),
        )
        self._conn.commit()
        return cur.lastrowid

    def search_memory(self, env_id: int, query: str, k: int = 5) -> list[tuple[str, float]]:
        q = self._embedder.embed(query)
        rows = self._conn.execute(
            "SELECT content, embedding FROM memories WHERE environment_id = ?", (env_id,)
        ).fetchall()
        scored = [(r["content"], cosine(q, json.loads(r["embedding"]))) for r in rows]
        scored.sort(key=lambda t: t[1], reverse=True)
        return [t for t in scored if t[1] > 0.0][:k]

    # --- auditoria -------------------------------------------------------

    def _audit(self, env_id: int | None, action: str, detail: str, result: str = "ok") -> None:
        self._conn.execute(
            "INSERT INTO audit_log(environment_id, action, detail, result) VALUES (?, ?, ?, ?)",
            (env_id, action, detail, result),
        )
        self._conn.commit()


def _env(row: sqlite3.Row) -> Environment:
    return Environment(row["id"], row["name"], row["kind"], row["description"])


def _incident(row: sqlite3.Row) -> Incident:
    return Incident(
        row["id"], row["environment_id"], row["title"], row["problem"],
        row["status"], row["root_cause"], row["resolution"],
    )
