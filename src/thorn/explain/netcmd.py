"""explain_ip / explain_ping — rodam o comando real (Linux) e anotam a saída.

Os parsers são funções puras (recebem o texto), então dá pra testar sem rede.
Os `explain_*` orquestram: rodam o comando via subprocess e chamam o parser.
"""

from __future__ import annotations

import re
import subprocess
import sys

from .steps import Step

_TIMEOUT = 8


def _run(argv: list[str]) -> tuple[bool, str]:
    if sys.platform.startswith("win"):
        return False, "esse comando roda na Kali (Linux) — no Windows não existe."
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=_TIMEOUT)
        return p.returncode == 0, (p.stdout or p.stderr)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)


# ---------------- ip addr ----------------

def parse_ip_addr(text: str) -> list[dict]:
    """Interfaces: nome, flags, ipv4, mac. Parser puro."""
    ifaces: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        m = re.match(r"^\d+:\s+([\w.@-]+):\s+<([^>]*)>", line)
        if m:
            cur = {"name": m.group(1).split("@")[0], "flags": m.group(2).split(","),
                   "ipv4": [], "mac": None}
            ifaces.append(cur)
            continue
        if cur is None:
            continue
        m = re.search(r"inet\s+([\d.]+/\d+)", line)
        if m:
            cur["ipv4"].append(m.group(1))
        m = re.search(r"link/\w+\s+([0-9a-f:]{17})", line)
        if m:
            cur["mac"] = m.group(1)
    return ifaces


def _explain_ip_addr(text: str) -> list[Step]:
    steps: list[Step] = []
    for it in parse_ip_addr(text):
        up = "UP" in it["flags"]
        role = "loopback (a própria máquina, 127.0.0.1)" if it["name"] == "lo" else "interface de rede"
        title = f"{it['name']}  [{'UP' if up else 'DOWN'}]  " + (", ".join(it["ipv4"]) or "sem IPv4")
        detail = []
        if it["mac"]:
            detail.append(f"MAC (endereço físico): {it['mac']}")
        steps.append(Step("IP", title,
            f"{role}. O IP com /máscara (ex: /24) diz a faixa da rede local; o MAC é o "
            "endereço físico da placa, usado dentro da mesma rede.", detail, ok=up or it["name"] == "lo"))
    if not steps:
        steps.append(Step("INFO", "nenhuma interface lida", "Saída inesperada do 'ip a'.", [text[:200]], ok=False))
    return steps


# ---------------- ip route ----------------

def parse_ip_route(text: str) -> tuple[str | None, list[str]]:
    """Retorna (gateway_default, lista_de_rotas). Parser puro."""
    gw = None
    routes = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        routes.append(line)
        m = re.match(r"default via ([\d.]+)", line)
        if m:
            gw = m.group(1)
    return gw, routes


def _explain_ip_route(text: str) -> list[Step]:
    gw, routes = parse_ip_route(text)
    steps = [Step("IP", f"gateway padrão: {gw or 'nenhum'}",
        "A tabela de rotas decide POR ONDE cada pacote sai. 'default via X' é o gateway: "
        "tudo que não for da rede local vai por ele (normalmente o roteador rumo à internet).",
        routes)]
    return steps


def explain_ip(args: list[str]) -> list[Step]:
    sub = (args[0] if args else "a").lower()
    if sub in ("r", "route"):
        ok, out = _run(["ip", "route"])
        return _explain_ip_route(out) if ok else [Step("INFO", "ip route falhou", "", [out], ok=False)]
    # default: ip addr
    ok, out = _run(["ip", "addr"])
    return _explain_ip_addr(out) if ok else [Step("INFO", "ip addr falhou", "", [out], ok=False)]


# ---------------- ping ----------------

def parse_ping(text: str) -> dict:
    """Extrai ip resolvido, ttl, perda e rtt. Parser puro."""
    out: dict = {}
    m = re.search(r"PING\s+\S+\s+\(([\d.]+)\)", text)
    if m:
        out["ip"] = m.group(1)
    m = re.search(r"ttl=(\d+)", text)
    if m:
        out["ttl"] = int(m.group(1))
    m = re.search(r"(\d+)%\s+packet loss", text)
    if m:
        out["loss"] = int(m.group(1))
    m = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)", text)
    if m:
        out["rtt_min"], out["rtt_avg"], out["rtt_max"] = (float(m.group(i)) for i in (1, 2, 3))
    return out


def _explain_ping(host: str, text: str) -> list[Step]:
    st = parse_ping(text)
    ip = st.get("ip", "?")
    loss = st.get("loss")
    avg = st.get("rtt_avg")
    ttl = st.get("ttl")
    ok = loss == 0 if loss is not None else False
    title = f"{host} → {ip}"
    if avg is not None:
        title += f"  ·  {avg:.0f} ms (média)"
    if loss is not None:
        title += f"  ·  {loss}% perda"
    detail = []
    if ttl is not None:
        detail.append(f"TTL={ttl} (saltos que o pacote ainda podia dar — cai 1 por roteador)")
    return [Step("ICMP", title,
        "O ping manda pacotes ICMP 'echo' e mede o tempo de ida e volta (RTT). Serve pra "
        "responder duas coisas: o host está VIVO? e a rede está RÁPIDA? Perda 0% = estável.",
        detail, ok=ok)]


def explain_ping(host: str) -> list[Step]:
    ok, out = _run(["ping", "-c", "3", host])
    if not out:
        return [Step("INFO", "ping falhou", "", ["sem saída"], ok=False)]
    return _explain_ping(host, out)
