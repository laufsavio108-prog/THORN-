"""THORN CLI (Typer/Rich).

Comandos do 0.1 giram em torno do diferencial: ambientes isolados + investigação
por incidentes similares. `thorn env`, `thorn incident`, `thorn investigate`.
"""

from __future__ import annotations

import sys

# O console do Windows abre em cp1252 e quebra ao imprimir glifos como "✓".
# Reconfigura stdout/stderr para UTF-8 (no Linux/Kali já é o default).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001 — best-effort, nunca deve derrubar a CLI
            pass

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .agent import AgentLoop
from .banner import render_banner
from .config import load_settings
from .llm import LlmGateway
from .memory import MemoryStore
from .tools import ToolDenied, build_registry

app = typer.Typer(
    help="THORN — Your Infrastructure Intelligence.",
    invoke_without_command=True,
    add_completion=False,
)
env_app = typer.Typer(help="Gerencia ambientes isolados.")
inc_app = typer.Typer(help="Registra e resolve incidentes.")
app.add_typer(env_app, name="env")
app.add_typer(inc_app, name="incident")

console = Console()


@app.callback()
def main(ctx: typer.Context) -> None:
    """Sem subcomando: mostra o splash + resumo."""
    if ctx.invoked_subcommand is None:
        render_banner(console)
        s = load_settings()
        ai = "[green]ligada[/]" if s.ai_enabled else "[yellow]off[/]"
        console.print(
            f"  IA: {ai}   •   ambientes: {len(_store().list_environments())}"
            "   •   [dim]thorn --help[/]\n"
        )


@app.command()
def banner() -> None:
    """Mostra o splash do THORN."""
    render_banner(console)


def _store() -> MemoryStore:
    s = load_settings()
    return MemoryStore(s.db_path)


def _require_env(store: MemoryStore, name: str):
    env = store.get_environment(name)
    if env is None:
        console.print(f"[red]Ambiente '{name}' não existe.[/] Crie com: thorn env create {name}")
        raise typer.Exit(1)
    return env


@app.command()
def version() -> None:
    """Mostra a versão."""
    console.print(f"THORN {__version__}")


@app.command()
def status() -> None:
    """Estado do THORN: ambientes e se a IA está ligada."""
    s = load_settings()
    store = _store()
    envs = store.list_environments()
    console.print(f"[bold]THORN {__version__}[/]  •  IA: "
                  + ("[green]ligada[/]" if s.ai_enabled else "[yellow]off (sem ANTHROPIC_API_KEY)[/]"))
    console.print(f"memória: {s.db_path}")
    console.print(f"ambientes: {len(envs)}")


@env_app.command("create")
def env_create(
    name: str,
    kind: str = typer.Option("personal", help="company | lab | personal"),
    description: str = typer.Option("", "--desc"),
) -> None:
    """Cria um ambiente isolado."""
    store = _store()
    if store.get_environment(name):
        console.print(f"[yellow]'{name}' já existe.[/]")
        raise typer.Exit(1)
    store.create_environment(name, kind, description)
    console.print(f"[green]✓[/] ambiente '{name}' ({kind}) criado.")


@env_app.command("list")
def env_list() -> None:
    """Lista os ambientes."""
    store = _store()
    table = Table("nome", "tipo", "descrição")
    for e in store.list_environments():
        table.add_row(e.name, e.kind, e.description or "—")
    console.print(table)


@inc_app.command("add")
def incident_add(env: str, title: str, problem: str = typer.Option(..., "--problem")) -> None:
    """Registra um incidente num ambiente."""
    store = _store()
    e = _require_env(store, env)
    inc = store.add_incident(e.id, title, problem)
    console.print(f"[green]✓[/] incidente #{inc.id} registrado em '{env}'.")


@inc_app.command("resolve")
def incident_resolve(
    incident_id: int,
    root_cause: str = typer.Option(..., "--cause"),
    resolution: str = typer.Option(..., "--fix"),
) -> None:
    """Marca um incidente como resolvido (vira material de investigação futura)."""
    store = _store()
    store.resolve_incident(incident_id, root_cause, resolution)
    console.print(f"[green]✓[/] incidente #{incident_id} resolvido.")


@app.command("tools")
def tools_list() -> None:
    """Lista as ferramentas que o THORN pode usar (as mesmas que o LLM verá)."""
    reg = build_registry()
    table = Table("tool", "descrição")
    for name in reg.names():
        table.add_row(name, reg.describe(name))
    console.print(table)


@app.command("exec")
def tool_exec(
    name: str,
    path: str = typer.Option(".", "--path", help="caminho, p/ tools como git_status"),
) -> None:
    """Executa uma tool passando pela policy (confirma ações sensíveis)."""
    reg = build_registry(confirm=_cli_confirm)
    try:
        out = reg.invoke(name, path=path)
    except ToolDenied as e:
        console.print(f"[red]negado:[/] {e}")
        raise typer.Exit(1)
    console.print(out)


def _cli_confirm(reason: str, argv: list[str]) -> bool:
    console.print(f"[yellow]ação sensível[/] ({reason}): [bold]{' '.join(argv)}[/]")
    return typer.confirm("executar?")


@app.command()
def investigate(env: str, problem: str) -> None:
    """Investiga um problema cruzando com incidentes similares do ambiente."""
    s = load_settings()
    store = _store()
    e = _require_env(store, env)
    loop = AgentLoop(store, LlmGateway(s))
    result = loop.investigate(e.id, problem)

    console.print(f"\n[bold]THORN / INVESTIGAÇÃO[/]  •  ambiente: [cyan]{env}[/]")
    console.print(f"problema: {problem}\n")

    if result.similar:
        table = Table("incidente similar", "score")
        for title, score in result.similar:
            table.add_row(title, f"{score:.2f}")
        console.print(table)
    else:
        console.print("[dim]nenhum incidente parecido neste ambiente.[/]")

    console.print(f"\n[bold]Recomendação[/]\n{result.recommendation}\n")


if __name__ == "__main__":
    app()
