"""explain — roda um comando de rede de verdade e o anota camada por camada.

Dispatcher: pelo primeiro token decide o explicador.
  curl/wget/http(s)/<url>  → DNS→TCP→TLS→HTTP  (explain_http)
  dig/nslookup/host <nome> → DNS               (explain_dns)
  ip [a|r]                 → interfaces/rotas   (explain_ip)
  ping <host>              → ICMP/RTT           (explain_ping)
"""

from __future__ import annotations

from .dns import explain_dns
from .http import explain_http
from .netcmd import explain_ip, explain_ping, explain_tcpdump, explain_traceroute
from .steps import LAYER_STYLE, Step

__all__ = ["run", "Step", "LAYER_STYLE", "explain_http", "explain_dns", "explain_ip",
           "explain_ping", "explain_traceroute", "explain_tcpdump"]

_HTTP_CMDS = {"curl", "wget"}
_DNS_CMDS = {"dig", "nslookup", "host"}


def _last_target(words: list[str]) -> str:
    """Último token que não é uma flag (o alvo: url/host)."""
    for w in reversed(words):
        if not w.startswith("-"):
            return w
    return ""


def run(words: list[str]) -> list[Step]:
    if not words:
        return [Step("INFO", "nada pra explicar",
            "Ex: thorn explain curl google.com", ok=False)]

    head = words[0].lower()

    if head in _HTTP_CMDS:
        return explain_http(_last_target(words[1:]) or "")
    if head in _DNS_CMDS:
        return explain_dns(_last_target(words[1:]) or "")
    if head == "ip":
        return explain_ip(words[1:])
    if head == "ping":
        return explain_ping(_last_target(words[1:]) or "")
    if head in ("traceroute", "tracert", "tracepath"):
        return explain_traceroute(_last_target(words[1:]) or "")
    if head == "tcpdump":
        return explain_tcpdump(words[1:])

    # sem comando reconhecido: se parece url/host, trata como HTTP
    if "." in head or "://" in head:
        return explain_http(words[0])

    return [Step("INFO", f"ainda não sei explicar '{head}'",
        "Cobertos: curl, wget, dig, nslookup, ip, ping, traceroute, tcpdump. "
        "Ex: thorn explain tcpdump port 443", ok=False)]
