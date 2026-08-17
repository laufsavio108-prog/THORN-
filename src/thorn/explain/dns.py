"""explain_dns — resolve um nome de verdade e mostra o resolver usado."""

from __future__ import annotations

import socket
from pathlib import Path

from .steps import Step


def read_resolvers(path: str = "/etc/resolv.conf") -> list[str]:
    """Nameservers configurados (Linux). No Windows o arquivo não existe → [] ."""
    try:
        out = []
        for line in Path(path).read_text().splitlines():
            line = line.strip()
            if line.startswith("nameserver"):
                out.append(line.split()[1])
        return out
    except OSError:
        return []


def explain_dns(host: str) -> list[Step]:
    steps: list[Step] = []
    resolvers = read_resolvers()
    src = f"resolver: {', '.join(resolvers)} (de /etc/resolv.conf)" if resolvers else "resolver: o do sistema"

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        steps.append(Step("DNS", f"não resolveu {host}",
            "NXDOMAIN/erro: o nome não existe ou o resolver não respondeu.", [str(e), src], ok=False))
        return steps

    v4 = [i[4][0] for i in infos if i[0] == socket.AF_INET]
    v6 = [i[4][0] for i in infos if i[0] == socket.AF_INET6]
    v4 = list(dict.fromkeys(v4))
    v6 = list(dict.fromkeys(v6))
    detail = [src]
    if v4:
        detail.append(f"IPv4 (registro A):    {', '.join(v4)}")
    if v6:
        detail.append(f"IPv6 (registro AAAA): {', '.join(v6)}")
    steps.append(Step(
        "DNS", f"{host} → {(v4 or v6)[0]}",
        "O DNS é a agenda da internet: traduz o NOME em IP. Seu PC pergunta ao resolver "
        "(normalmente o roteador), que pergunta em cadeia até achar a resposta. "
        "É o que 'dig' e 'nslookup' mostram.",
        detail,
    ))
    return steps
