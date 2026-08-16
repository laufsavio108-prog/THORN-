# THORN

**Your Infrastructure Intelligence.** Observe. Analyze. Guide. You operate.

THORN é um copiloto pessoal de infraestrutura e segurança. Ele acompanha suporte,
infra, cloud, security, DevOps e aprendizado — acumulando contexto ao longo da sua
carreira. O agente **recomenda**; **você executa** as ações sensíveis.

> Sucessor do protótipo `chronos` (TypeScript). Reescrito em Python. O 0.1 é
> deliberadamente pequeno: prova o diferencial (memória por ambiente + "esse
> incidente parece com N anteriores") antes de trazer FastAPI, Postgres, Redis,
> Connector e observabilidade.

## Diferencial

A memória do THORN é **separada por ambiente**. Uma informação da Empresa A nunca
aparece quando você está trabalhando no Lab pessoal ou na Empresa B. E quando você
descreve um problema, o THORN busca semanticamente entre os incidentes **daquele
ambiente** e diz de quais casos passados ele se parece.

```
Ambientes (isolados)
├── empresa-a      (company)
├── empresa-b      (company)
└── lab-pessoal    (personal)   ← Kali, Docker, etc.
```

## 0.1 — o que existe

- **Core desacoplado:** `memory` / `tools` / `security` (policy) / `llm` / `agent`.
- **Memória:** SQLite local + embeddings plugáveis. Isolamento por ambiente é
  invariante em toda query.
- **Busca de incidente similar:** cosseno sobre embeddings, escopado ao ambiente.
- **Fronteira Tool ↔ Permissão:** portada do chronos — SAFE / CONFIRM / BLOCKED por
  argumento, não por binário. O agente pede confirmação em ações sensíveis.
- **CLI (Typer/Rich):** cria ambiente, registra/resolve incidente, busca similares.

## O que NÃO está no 0.1 (de propósito)

FastAPI / web, Postgres+pgvector, Redis, ARQ/workers, THORN Connector, mTLS,
OpenTelemetry/Prometheus/Grafana. Entram quando doer a falta — não no dia 1.

## Rodando

```bash
cd thorn
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
thorn --help
```

Sem `ANTHROPIC_API_KEY` o THORN roda em modo determinístico (memória + policy
funcionam; o loop de IA fica "off"). Com a key, o gateway usa `claude-opus-5`.

## Testes

```bash
pytest
```
