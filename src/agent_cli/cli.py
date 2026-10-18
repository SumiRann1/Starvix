import asyncio

import typer
from rich.console import Console

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
def chat():
    """Start an interactive Forge chat session."""
    try:
        asyncio.run(chat_main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat interrupted.[/yellow]")

if __name__ == "__main__":
    app()
