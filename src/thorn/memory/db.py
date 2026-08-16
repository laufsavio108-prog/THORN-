"""Conexão SQLite e schema da memória do THORN.

Local-first, single-user: o banco vive em ~/.thorn/thorn.db. Não há multi-tenant
nem exposição de rede — o isolamento entre ambientes é lógico (environment_id em
toda query), não uma fronteira de segurança de rede.

O schema é embutido aqui como constante (em vez de um .sql separado) para não
precisar empacotar dado de pacote e para manter o 0.1 em um único módulo.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# INVARIANTE: todo conhecimento pertence a UM ambiente. Nenhuma leitura de
# incidents/memories pode cruzar environment_id — é isso que impede a Empresa A
# de vazar contexto na Empresa B ou no lab pessoal.
SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS environments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    kind        TEXT    NOT NULL DEFAULT 'personal',   -- company | lab | personal
    description TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS incidents (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id INTEGER NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
    title          TEXT    NOT NULL,
    problem        TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'open',     -- open | investigating | resolved
    root_cause     TEXT,
    resolution     TEXT,
    embedding      TEXT    NOT NULL,                    -- JSON: vetor de title+problem
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    resolved_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_incidents_env    ON incidents(environment_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(environment_id, status);

CREATE TABLE IF NOT EXISTS memories (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id INTEGER NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
    kind           TEXT    NOT NULL DEFAULT 'technical', -- personal | work | technical
    content        TEXT    NOT NULL,
    source         TEXT    NOT NULL DEFAULT 'user',      -- user | incident | ai_inference | doc
    embedding      TEXT    NOT NULL,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_memories_env ON memories(environment_id);

CREATE TABLE IF NOT EXISTS audit_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id INTEGER REFERENCES environments(id) ON DELETE SET NULL,
    action         TEXT    NOT NULL,
    detail         TEXT    NOT NULL DEFAULT '',
    result         TEXT    NOT NULL DEFAULT 'ok',        -- ok | denied | error
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_audit_env ON audit_log(environment_id, created_at);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Abre (criando se preciso) o banco e garante o schema. Row factory por nome."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    return conn
