"""Testes do explain — parsers puros (sem rede) + roteamento do dispatcher."""

from __future__ import annotations

from thorn import explain
from thorn.explain.http import parse_url
from thorn.explain.netcmd import (
    estimate_hops,
    parse_ip_addr,
    parse_ip_route,
    parse_ping,
    parse_tcpdump,
    parse_traceroute,
)

# --- parse_url ---------------------------------------------------------


def test_url_sem_scheme_vira_https() -> None:
    assert parse_url("google.com") == ("https", "google.com", 443, "/")


def test_url_http_porta_80() -> None:
    assert parse_url("http://exemplo.com/pag") == ("http", "exemplo.com", 80, "/pag")


# --- ip addr / route ---------------------------------------------------

_IP_ADDR = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
2: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 08:00:27:ab:cd:ef brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.101/24 brd 192.168.56.255 scope global eth1
"""

_IP_ROUTE = """default via 10.0.2.2 dev eth0 proto dhcp metric 100
192.168.56.0/24 dev eth1 proto kernel scope link src 192.168.56.101
"""


def test_parse_ip_addr() -> None:
    ifaces = parse_ip_addr(_IP_ADDR)
    assert [i["name"] for i in ifaces] == ["lo", "eth1"]
    eth1 = ifaces[1]
    assert eth1["ipv4"] == ["192.168.56.101/24"]
    assert eth1["mac"] == "08:00:27:ab:cd:ef"
    assert "UP" in eth1["flags"]


def test_parse_ip_route_acha_gateway() -> None:
    gw, routes = parse_ip_route(_IP_ROUTE)
    assert gw == "10.0.2.2"
    assert len(routes) == 2


# --- ping --------------------------------------------------------------

_PING = """PING google.com (142.250.79.14) 56(84) bytes of data.
64 bytes from rio01s21 (142.250.79.14): icmp_seq=1 ttl=115 time=12.3 ms
--- google.com ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2003ms
rtt min/avg/max/mdev = 12.0/12.5/13.1/0.4 ms
"""


def test_parse_ping() -> None:
    st = parse_ping(_PING)
    assert st["ip"] == "142.250.79.14"
    assert st["ttl"] == 115
    assert st["loss"] == 0
    assert st["rtt_avg"] == 12.5


_TRACE = """traceroute to google.com (142.250.79.14), 20 hops max, 60 byte packets
 1  10.0.2.2  0.234 ms
 2  *
 3  100.65.0.1  10.512 ms
 4  142.250.79.14  12.001 ms
"""


def test_parse_traceroute() -> None:
    hops = parse_traceroute(_TRACE)
    assert len(hops) == 4
    assert hops[0]["ip"] == "10.0.2.2"
    assert hops[1]["timeout"] is True   # a linha com *
    assert hops[3]["ip"] == "142.250.79.14"
    assert hops[3]["ms"] == 12.001


_TCPDUMP = """12:00:01.111 IP 10.0.2.15.43210 > 142.250.79.14.443: Flags [S], seq 1, win 64240
12:00:01.222 IP 142.250.79.14.443 > 10.0.2.15.43210: Flags [S.], seq 9, ack 2
12:00:01.333 IP 10.0.2.15.55000 > 8.8.8.8.53: UDP, length 34
12:00:01.444 ARP, Request who-has 10.0.2.2 tell 10.0.2.15, length 28
14 packets captured
"""


def test_parse_tcpdump() -> None:
    pkts = parse_tcpdump(_TCPDUMP)
    protos = [p["proto"] for p in pkts]
    assert protos == ["TCP", "TCP", "UDP", "ARP"]  # a linha de status é ignorada
    assert pkts[0]["flags"] == "S"                  # SYN puro
    assert pkts[0]["src"] == "10.0.2.15.43210"


def test_estimate_hops() -> None:
    # TTL 250 → começou em 255 → 5 saltos (o caso que o usuário viu)
    assert estimate_hops(250) == (5, 255)
    # TTL 115 → começou em 128 → 13 saltos
    assert estimate_hops(115) == (13, 128)
    # TTL 60 → começou em 64 → 4 saltos
    assert estimate_hops(60) == (4, 64)


# --- dispatcher --------------------------------------------------------


def test_dispatch_target_ignora_flags() -> None:
    from thorn.explain import _last_target
    assert _last_target(["-v", "-s", "google.com"]) == "google.com"


def test_dispatch_comando_desconhecido() -> None:
    steps = explain.run(["banana"])
    assert steps and steps[0].ok is False
