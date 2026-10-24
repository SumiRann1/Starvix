import asyncio

import typer
from rich.console import Console

from .chat import get_all_threads
from .chat import main as chat_main

app = typer.Typer(
    name="forge",
    help="Forge — a local-first LangGraph agent runtime.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


@app.callback()
def main():
    """Forge — a local-first LangGraph agent runtime."""
    return


@app.command()
def status():
    """Show Forge runtime status."""
    console.print("[bold]Forge Agent Runtime[/bold]")
    console.print("CLI initialized successfully.")
    console.print("Model execution and persistent storage are separate milestones.")


@app.command()
def threads():
    """List all saved conversation threads."""
    saved_threads = get_all_threads()
    if not saved_threads:
        console.print("[dim]No saved threads found.[/dim]")
        return
    console.print("[bold]Saved conversation threads:[/bold]")
    for tid in saved_threads:
        console.print(f"  - [cyan]{tid}[/cyan]")
    console.print("\n[dim]To resume a thread, run:[/dim] forge chat --thread <id>")


@app.command()
def chat(
    thread: str | None = typer.Option(
        None,
        "--thread",
        "-t",
        help="Thread ID to use or resume. If omitted, a new random session is created.",
    ),
):
    """Start an interactive Forge chat session."""
    try:
        asyncio.run(chat_main(thread_id=thread))
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat interrupted.[/yellow]")


if __name__ == "__main__":
    app()
