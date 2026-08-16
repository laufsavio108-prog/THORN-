"""LLM Gateway — camada fina sobre a SDK da Anthropic.

Import da SDK é lazy: o THORN roda (memória + policy + tools) sem key nenhuma.
Modelo default claude-opus-5 com thinking adaptativo. Trocar de modelo/provedor
depois é mexer só aqui — o resto do THORN não sabe qual LLM está por baixo.
"""

from __future__ import annotations

from ..config import Settings


class LlmUnavailable(Exception):
    """Sem ANTHROPIC_API_KEY: o loop de IA fica desligado, o resto funciona."""


class LlmGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None  # criado sob demanda

    @property
    def available(self) -> bool:
        return self._settings.ai_enabled

    def _ensure_client(self):
        if not self.available:
            raise LlmUnavailable(
                "Sem ANTHROPIC_API_KEY. Exporte a key própria do THORN para ligar o loop de IA."
            )
        if self._client is None:
            import anthropic  # import lazy: não exige a SDK carregada sem key

            self._client = anthropic.Anthropic()
        return self._client

    def complete(self, system: str, prompt: str, max_tokens: int = 4096) -> str:
        client = self._ensure_client()
        resp = client.messages.create(
            model=self._settings.model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
