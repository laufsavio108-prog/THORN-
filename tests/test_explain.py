"""Testes do explain — parsers puros (sem rede) + roteamento do dispatcher."""

from __future__ import annotations

from thorn import explain
from thorn.explain.http import parse_url
from thorn.explain.netcmd import parse_ip_addr, parse_ip_route, parse_ping

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


# --- dispatcher --------------------------------------------------------


def test_dispatch_target_ignora_flags() -> None:
    from thorn.explain import _last_target
    assert _last_target(["-v", "-s", "google.com"]) == "google.com"


def test_dispatch_comando_desconhecido() -> None:
    steps = explain.run(["banana"])
    assert steps and steps[0].ok is False
