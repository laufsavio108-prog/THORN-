"""Splash do THORN — bloco ASCII + borda, no estilo Jarvis/terminal."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
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


def _block(word: str, gap: str = "  ") -> Text:
    rows = []
    for i in range(5):
        rows.append(gap.join(_LETTERS[ch][i] for ch in word))
    return Text("\n".join(rows), style="bold white")


def render_banner(console: Console) -> None:
    body = Group(
        Align.center(_block("THORN")),
        Text(""),
        Align.center(Text("INFRASTRUCTURE  •  CLOUD  •  SECURITY", style="bold grey70")),
        Text(""),
        Align.center(Text(f"◇  THORN v{__version__}  ◇", style="cyan")),
    )
    console.print(
        Panel(body, border_style="grey42", padding=(1, 4), expand=False)
    )
