"""AgentLoop (esqueleto do 0.1).

A ideia de investigação do THORN: dado um problema num ambiente, primeiro
recupera incidentes similares DAQUELE ambiente (o diferencial), monta contexto e
— se houver LLM — pede uma hipótese + próximo passo. O agente RECOMENDA; quem
executa tool sensível passa pelo ToolRegistry/PermissionEngine.

No 0.1 o loop de tool-use completo (modelo chamando tools) ainda não está ligado;
o que está provado é: memória por ambiente → contexto → recomendação.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..llm.gateway import LlmGateway, LlmUnavailable
from ..memory.store import MemoryStore

_SYSTEM = (
    "Você é o THORN, um copiloto de infraestrutura e segurança. Observe, analise e "
    "GUIE — o operador executa as ações. Baseie hipóteses nos incidentes passados "
    "fornecidos; seja específico sobre o próximo teste a fazer."
)


@dataclass
class Investigation:
    problem: str
    similar: list[tuple[str, float]]  # (título do incidente, score)
    recommendation: str


class AgentLoop:
    def __init__(self, store: MemoryStore, llm: LlmGateway) -> None:
        self._store = store
        self._llm = llm

    def investigate(self, env_id: int, problem: str) -> Investigation:
        hits = self._store.similar_incidents(env_id, problem, k=5)
        similar = [(h.incident.title, round(h.score, 3)) for h in hits]

        context = "\n".join(
            f"- {h.incident.title} → causa: {h.incident.root_cause or 'não resolvida'}"
            for h in hits
        ) or "(nenhum incidente parecido neste ambiente)"

        if self._llm.available:
            try:
                rec = self._llm.complete(
                    _SYSTEM,
                    f"Problema atual:\n{problem}\n\nIncidentes passados deste ambiente:\n{context}\n\n"
                    "Dê 1 hipótese provável e o próximo teste concreto.",
                )
            except LlmUnavailable:
                rec = _offline_recommendation(hits)
        else:
            rec = _offline_recommendation(hits)

        return Investigation(problem, similar, rec)


def _offline_recommendation(hits: list) -> str:
    if not hits:
        return "IA desligada e sem incidentes parecidos. Registre este caso ao resolver."
    top = hits[0].incident
    causa = top.root_cause or "ainda não resolvida"
    return (
        f"IA desligada. Caso mais parecido: “{top.title}” (causa: {causa}). "
        "Investigue pela mesma trilha primeiro."
    )
