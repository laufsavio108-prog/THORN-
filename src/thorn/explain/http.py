"""explain_http — caminha uma requisição pela pilha real e anota cada camada.

Faz DNS → TCP → TLS → HTTP de verdade (stdlib socket/ssl), mostrando o IP que
resolveu, o tempo do handshake, a versão do TLS + certificado e o status HTTP.
É o 'curl google.com' explicado camada por camada.
"""

from __future__ import annotations

import socket
import ssl
import time
from urllib.parse import urlsplit

from .steps import Step


def parse_url(raw: str, default_scheme: str = "https") -> tuple[str, str, int, str]:
    """Quebra a URL em (scheme, host, porta, path). Sem scheme → https (pra mostrar TLS)."""
    if "://" not in raw:
        raw = f"{default_scheme}://{raw}"
    p = urlsplit(raw)
    scheme = p.scheme or default_scheme
    host = p.hostname or ""
    port = p.port or (443 if scheme == "https" else 80)
    path = p.path or "/"
    if p.query:
        path += "?" + p.query
    return scheme, host, port, path


def _common_name(field) -> str:
    if not field:
        return "?"
    d: dict[str, str] = {}
    for rdn in field:
        for k, v in rdn:
            d[k] = v
    return d.get("commonName") or d.get("organizationName") or "?"


def explain_http(raw_url: str) -> list[Step]:
    scheme, host, port, path = parse_url(raw_url)
    if not host:
        return [Step("INFO", f"URL inválida: {raw_url!r}", "Informe algo como 'google.com' ou 'https://site.com/pagina'.", ok=False)]

    steps: list[Step] = []
    scheme_note = ""
    if "://" not in raw_url and scheme == "https":
        scheme_note = "  (sem http/https na URL → usei https:443 pra te mostrar a camada TLS)"

    # 1) DNS ------------------------------------------------------------
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        steps.append(Step("DNS", f"não resolveu {host}",
            "O DNS traduz NOME → IP. Falhou: nome errado ou sem internet.", [str(e)], ok=False))
        return steps
    ips: list[str] = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    target = ips[0]
    steps.append(Step(
        "DNS", f"{host} → {target}{scheme_note}",
        "1ª camada. O DNS traduz o NOME (google.com) para um ENDEREÇO IP — sem isso a "
        "máquina não sabe pra quem falar. É o que o 'dig google.com' faz.",
        [f"outros IPs: {', '.join(ips[1:])}"] if len(ips) > 1 else [],
    ))

    # 2) TCP ------------------------------------------------------------
    sock = socket.socket(socket.AF_INET6 if ":" in target else socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(8)
    t0 = time.perf_counter()
    try:
        sock.connect((target, port))
    except OSError as e:
        steps.append(Step("TCP", f"não conectou em {target}:{port}",
            "TCP abre a conexão. Falhou: porta fechada, firewall ou host fora do ar.", [str(e)], ok=False))
        sock.close()
        return steps
    dt = (time.perf_counter() - t0) * 1000
    steps.append(Step(
        "TCP", f"conectado a {target}:{port} em {dt:.0f} ms",
        "2ª camada. O TCP abre a conexão com o aperto de mão de 3 vias (SYN → SYN-ACK → "
        "ACK). Garante que os dois lados estão prontos e que os dados chegam em ordem.",
    ))

    # 3) TLS ------------------------------------------------------------
    stream = sock
    if scheme == "https":
        ctx = ssl.create_default_context()
        try:
            stream = ctx.wrap_socket(sock, server_hostname=host)
        except ssl.SSLError as e:
            steps.append(Step("TLS", "handshake TLS falhou",
                "O TLS valida o certificado do servidor. Falhou: certificado inválido/expirado.", [str(e)], ok=False))
            sock.close()
            return steps
        cert = stream.getpeercert() or {}
        steps.append(Step(
            "TLS", f"{stream.version()} · {stream.cipher()[0]}",
            "3ª camada. O TLS é o 's' de httpS: cifra tudo, valida que o servidor é mesmo "
            "quem diz ser (certificado) e negocia uma chave secreta. Em http puro isso não existe.",
            [
                f"certificado p/: {_common_name(cert.get('subject'))}",
                f"emitido por: {_common_name(cert.get('issuer'))}",
                f"válido até: {cert.get('notAfter', '?')}",
            ],
        ))
    else:
        steps.append(Step("TLS", "sem TLS — http puro na porta 80",
            "Você usou http:// → nada é cifrado, qualquer um no caminho lê o tráfego. "
            "Por isso sites sérios te redirecionam pro https (veja o status abaixo)."))

    # 4) HTTP -----------------------------------------------------------
    req = (
        f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
        "User-Agent: THORN/0.1\r\nConnection: close\r\n\r\n"
    )
    try:
        stream.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf and len(buf) < 16384:
            chunk = stream.recv(2048)
            if not chunk:
                break
            buf += chunk
    except OSError as e:
        steps.append(Step("HTTP", "erro na troca HTTP", "Enviamos o GET mas a leitura falhou.", [str(e)], ok=False))
        stream.close()
        return steps
    head = buf.split(b"\r\n\r\n", 1)[0].decode(errors="replace")
    lines = head.split("\r\n")
    status = lines[0] if lines else "(sem resposta)"
    wanted = ("server:", "location:", "content-type:")
    detail = [ln for ln in lines[1:] if ln.lower().startswith(wanted)]
    steps.append(Step(
        "HTTP", status,
        "4ª camada. O HTTP é o pedido em si: mandamos 'GET " + path + "' e o servidor "
        "respondeu com um status (200 OK, 301 redirect, 404...) e cabeçalhos. É aqui que o conteúdo trafega.",
        detail,
    ))
    stream.close()
    return steps
