"""explain_ip / explain_ping — rodam o comando real (Linux) e anotam a saída.

Os parsers são funções puras (recebem o texto), então dá pra testar sem rede.
Os `explain_*` orquestram: rodam o comando via subprocess e chamam o parser.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

from .steps import Step

_TIMEOUT = 8


def _run(argv: list[str], timeout: int = _TIMEOUT) -> tuple[bool, str]:
    if sys.platform.startswith("win"):
        return False, "esse comando roda na Kali (Linux) — no Windows não existe."
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return p.returncode == 0, (p.stdout or p.stderr)
    except FileNotFoundError:
        return False, f"'{argv[0]}' não está instalado (tente: sudo apt install {argv[0]})"
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


def estimate_hops(ttl: int) -> tuple[int, int]:
    """Estima (saltos, ttl_inicial) a partir do TTL que CHEGOU.

    O TTL começa num padrão (64 Linux, 128 Windows, 255 rede) e cada roteador
    tira 1. Então saltos = inicial_provável − ttl_recebido. Parser puro.
    """
    for initial in (64, 128, 255):
        if ttl <= initial:
            return initial - ttl, initial
    return 0, ttl


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
        hops, initial = estimate_hops(ttl)
        detail.append(
            f"TTL={ttl}: começou provavelmente em {initial} e perdeu {hops} "
            f"→ quem respondeu está a ~{hops} roteador(es) de você"
        )
    return [Step("ICMP", title,
        "O ping manda pacotes ICMP 'echo' e mede o tempo de ida e volta (RTT). Responde "
        "duas coisas: o host está VIVO? e a rede está RÁPIDA? (perda 0% = estável). O TTL "
        "não é 'quanto falta pra chegar' — é um contador que cai 1 por roteador; comparando "
        "com o valor inicial padrão dá pra estimar a DISTÂNCIA em saltos.",
        detail, ok=ok)]


def explain_ping(host: str) -> list[Step]:
    ok, out = _run(["ping", "-c", "3", host])
    if not out:
        return [Step("INFO", "ping falhou", "", ["sem saída"], ok=False)]
    return _explain_ping(host, out)


# ---------------- traceroute ----------------

def parse_traceroute(text: str) -> list[dict]:
    """Cada salto: {num, ip, ms, timeout}. Parser puro."""
    hops: list[dict] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\s+(.*)$", line)
        if not m:
            continue
        num = int(m.group(1))
        rest = m.group(2)
        ip_m = re.search(r"\d+\.\d+\.\d+\.\d+", rest)
        ms_m = re.search(r"([\d.]+)\s*ms", rest)
        hops.append({
            "num": num,
            "ip": ip_m.group(0) if ip_m else None,
            "ms": float(ms_m.group(1)) if ms_m else None,
            "timeout": ip_m is None,
        })
    return hops


def _is_private(ip: str | None) -> bool:
    return bool(ip and (ip.startswith("10.") or ip.startswith("192.168.")
                        or re.match(r"172\.(1[6-9]|2\d|3[01])\.", ip)))


def _explain_traceroute(host: str, text: str) -> list[Step]:
    hops = parse_traceroute(text)
    if not hops:
        return [Step("INFO", "traceroute sem saltos", "", [text[:200]], ok=False)]

    last = hops[-1]
    reached = not last["timeout"]
    last_resp = max((i for i, h in enumerate(hops) if not h["timeout"]), default=-1)

    detail = []
    for i, h in enumerate(hops):
        # colapsa a fileira final de timeouts numa linha só
        if not reached and i > last_resp:
            faltam = len(hops) - i
            ini = hops[i]["num"]
            detail.append(f"{ini}–{last['num']}. sem resposta ({faltam} saltos até o teto)")
            break
        if h["timeout"]:
            detail.append(f"{h['num']:>2}. *   (roteador não respondeu)")
        else:
            t = f"{h['ms']:.0f} ms" if h["ms"] is not None else ""
            detail.append(f"{h['num']:>2}. {h['ip']:<18} {t}")

    title = f"caminho até {host}: {len(hops)} saltos"
    if reached:
        title += f" (chegou em {last['ip']})"
    steps = [Step("IP", title,
        "O traceroute usa o truque do TTL: manda pacotes com TTL=1, depois 2, 3... "
        "Cada roteador que zera o TTL responde 'Time Exceeded' e se revela — assim ele "
        "mapeia roteador por roteador o caminho até o destino. Linhas com * = não respondeu.",
        detail, ok=reached)]

    # diagnóstico: só o 1º salto (privado) respondeu → provável NAT engolindo o traceroute
    responded = [h for h in hops if not h["timeout"]]
    if not reached and last_resp <= 0 and responded and _is_private(responded[0]["ip"]):
        steps.append(Step("INFO", "só o 1º salto respondeu — o NAT está engolindo o traceroute",
            f"O salto 1 ({responded[0]['ip']}) é o roteador NAT da sua VM (VirtualBox). O NAT "
            "do VirtualBox não repassa os pacotes do traceroute, então os saltos seguintes "
            "somem. Não é erro do THORN nem da sua internet. Pra ver o caminho completo: "
            "rode 'tracert google.com' no Windows (host), OU ponha a VM em rede 'Bridge'. "
            "Dentro da VM, o modo TCP costuma furar o NAT: sudo traceroute -T -p 443 " + host,
            ok=False))
    return steps


def explain_traceroute(host: str) -> list[Step]:
    # -n numérico (rápido) · -q 1 uma sonda/salto · -w 2 espera 2s · -m 20 teto de saltos
    ok, out = _run(["traceroute", "-n", "-q", "1", "-w", "2", "-m", "20", host], timeout=60)
    if not out:
        return [Step("INFO", "traceroute falhou", "", ["sem saída"], ok=False)]
    if "não está instalado" in out or "not found" in out.lower():
        return [Step("INFO", "traceroute não instalado", "Instale com: sudo apt install traceroute", [out], ok=False)]
    return _explain_traceroute(host, out)


# ---------------- tcpdump ----------------

def parse_tcpdump(text: str) -> list[dict]:
    """Cada pacote: {proto, src, dst, flags}. Parser puro."""
    pkts: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0].isalpha() and not re.match(r"\d{2}:\d{2}:\d{2}", line):
            # linhas de status do tcpdump (ex: "N packets captured") não são pacotes
            if "ARP" not in line:
                continue
        if "ARP" in line:
            pkts.append({"proto": "ARP", "src": None, "dst": None, "flags": None})
            continue
        m = re.search(r"IP6?\s+(\S+?)\s+>\s+(\S+?):", line)
        src, dst = (m.group(1), m.group(2)) if m else (None, None)
        if "ICMP" in line:
            proto = "ICMP"
        elif "UDP" in line or re.search(r"\.53\b", line):
            proto = "UDP"
        elif "Flags [" in line or "tcp" in line.lower():
            proto = "TCP"
        elif m:
            proto = "IP"
        else:
            continue
        fm = re.search(r"Flags \[([^\]]*)\]", line)
        pkts.append({"proto": proto, "src": src, "dst": dst, "flags": fm.group(1) if fm else None})
    return pkts


def _explain_tcpdump(text: str) -> list[Step]:
    pkts = parse_tcpdump(text)
    if not pkts:
        return [Step("INFO", "nenhum pacote capturado",
            "A rede estava quieta ou faltou permissão. Gere tráfego (ex.: um 'ping 8.8.8.8' "
            "ou 'curl google.com' em OUTRO terminal) e rode de novo.", [text[:200]], ok=False)]

    counts: dict[str, int] = {}
    syns = 0
    for p in pkts:
        counts[p["proto"]] = counts.get(p["proto"], 0) + 1
        if p["flags"] and "S" in p["flags"] and "." not in p["flags"]:
            syns += 1
    resumo = "  ·  ".join(f"{k}: {v}" for k, v in sorted(counts.items(), key=lambda x: -x[1]))

    detail = [f"protocolos: {resumo}"]
    if syns:
        detail.append(f"{syns} pacote(s) SYN → conexões TCP começando (o 1º passo do handshake)")
    for p in pkts[:6]:
        if p["src"]:
            fl = f" [{p['flags']}]" if p["flags"] else ""
            detail.append(f"{p['proto']:<5} {p['src']} → {p['dst']}{fl}")
        else:
            detail.append(f"{p['proto']:<5} (broadcast/descoberta de vizinho)")

    return [Step("IP", f"{len(pkts)} pacotes capturados",
        "O tcpdump é o raio-x da rede: mostra os pacotes CRUS passando na placa, ao vivo. "
        "Cada linha é um pacote real — quem falou com quem, em qual protocolo. É a ferramenta "
        "de quem quer VER o que está acontecendo no fio (não só se 'funciona').",
        detail)]


def explain_tcpdump(extra: list[str]) -> list[Step]:
    # captura curta e com teto: -c 14 pacotes, e 'timeout 12' encerra se a rede estiver quieta.
    # ORDEM IMPORTA: sudo por FORA (controla o terminal e esconde a senha), timeout por DENTRO
    # (limita só o tcpdump, DEPOIS da autenticação). O contrário faz a senha vazar na tela.
    filtro = [w for w in extra if w]  # filtro opcional do usuário: ex "port 443", "icmp"
    argv = ["timeout", "12", "tcpdump", "-n", "-c", "14", "-i", "any"] + filtro
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        argv = ["sudo"] + argv

    ok, out = _run(argv, timeout=30)
    if "não está instalado" in out or "command not found" in out.lower():
        return [Step("INFO", "tcpdump não instalado", "Instale com: sudo apt install tcpdump", [out], ok=False)]
    if "permission" in out.lower() or "sudo:" in out.lower() or "password" in out.lower():
        return [Step("INFO", "precisa de root",
            "Capturar pacotes exige privilégio. Rode 'thorn explain tcpdump' no SEU terminal "
            "(interativo) — o THORN chama o tcpdump via sudo e o sudo vai pedir sua senha ali. "
            "Não prefixe 'sudo thorn' (o thorn vive no venv, o root não o acha no PATH).",
            [out.strip()[:160]], ok=False)]
    return _explain_tcpdump(out)
