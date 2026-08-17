"""Splash + home do THORN — bloco ASCII, identidade e menu de comandos."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__

# Fonte de bloco 5x5 por letra (█ = preenchido).
_LETTERS = {
    "T": ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    "H": ["█   █", "█   █", "█████", "█   █", "█   █"],
    "O": ["█████", "█   █", "█   █", "█   █", "█████"],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
}

# Menu de comandos: (grupo, [(comando, descrição)]).
_MENU = [
    ("investigar", [
        ('thorn investigate <amb> "<problema>"', "cruza o problema com incidentes passados do ambiente"),
    ]),
    ("memória por ambiente", [
        ("thorn env create/list", "ambientes isolados (empresa, lab, pessoal)"),
        ("thorn incident add/resolve", "registra incidentes e vira base de conhecimento"),
    ]),
    ("rede — explica AO VIVO", [
        ("thorn explain curl google.com", "caminha DNS → TCP → TLS → HTTP com dados reais"),
        ("thorn explain ip r · ping · traceroute", "rotas/gateway, latência e caminho até o destino"),
    ]),
    ("referência", [
        ("thorn ref [-l]", "catálogo Linux + Git offline (busca tolera acento)"),
    ]),
    ("ferramentas", [
        ("thorn tools · exec <tool>", "system_info, processos (/proc), git_status"),
    ]),
]


def _block(word: str, gap: str = "  ") -> Text:
    lines = [gap.join(_LETTERS[ch][i] for ch in word) for i in range(5)]
    return Text("\n".join(lines), style="bold white")


def render_banner(console: Console) -> None:
    body = Group(
        Align.center(_block("THORN")),
        Text(""),
        Align.center(Text("INFRASTRUCTURE  •  CLOUD  •  SECURITY", style="bold grey70")),
        Text(""),
        Align.center(Text(f"◇  THORN v{__version__}  ◇", style="cyan")),
    )
    console.print(Panel(body, border_style="grey42", padding=(1, 4), expand=False))


def render_home(console: Console, *, ai_enabled: bool, env_count: int, db_path: str) -> None:
    render_banner(console)

    console.print(
        "  [italic grey70]Copiloto de infraestrutura & segurança. "
        "Ele observa, analisa e guia — você opera.[/]\n"
    )

    ai = "[green]● ligada[/]" if ai_enabled else "[yellow]○ desligada[/]"
    console.print(
        f"  [bold]estado[/]   IA {ai}    ·    ambientes [cyan]{env_count}[/]"
        f"    ·    memória [dim]{db_path}[/]\n"
    )

    table = Table(box=None, padding=(0, 2, 0, 2), show_header=False)
    table.add_column(justify="left", no_wrap=True)
    table.add_column(justify="left", style="grey70")
    for idx, (grupo, itens) in enumerate(_MENU):
        if idx:
            table.add_section()
        table.add_row(Text(grupo.upper(), style="bold cyan"), "")
        for cmd, desc in itens:
            table.add_row(Text(cmd, style="bold"), desc)
    console.print(table)

    console.print("\n  [dim]ajuda detalhada: thorn --help   ·   thorn <comando> --help[/]\n")
