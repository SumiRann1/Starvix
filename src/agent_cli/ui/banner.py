from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent_cli.config import settings


def display_welcome_banner(
    config: dict,
    tools: list | None = None,
    console: Console | None = None,
) -> None:
    """Display a rich, professional welcome banner inspired by modern CLI tools."""
    con = console or Console()

    configurable = config.get("configurable", {}) if config else {}
    current_model = configurable.get("model") or settings.current_model
    thread_id = configurable.get("thread_id", "default")
    tools_list = tools or []
    tool_names = [getattr(t, "name", str(t)) for t in tools_list]
    tools_str = f"{len(tool_names)} active ({', '.join(tool_names[:3])}{'...' if len(tool_names) > 3 else ''})" if tool_names else "None"

    try:
        workspace_display = str(Path.cwd().name)
    except Exception: # noqa: BLE001
        workspace_display = "workspace"

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", justify="right")
    grid.add_column(style="white")

    grid.add_row("🤖 Model:", current_model)
    grid.add_row("🧵 Thread:", f"Thread: {thread_id}")
    grid.add_row("🛠️  Tools:", tools_str)
    grid.add_row("📂 Workspace:", workspace_display)

    panel = Panel(
        grid,
        title="[bold magenta]⚡ FORGE[/bold magenta] [bold white]ChatBot CLI[/bold white] [dim]v0.1.0[/dim]",
        subtitle="[dim]Type [cyan]/help[/cyan] for commands • [cyan]/exit[/cyan] to quit • [cyan]Tab[/cyan] autocomplete • [cyan]@[/cyan] attach files[/dim]",
        border_style="cyan",
        padding=(1, 2),
    )
    con.print(panel)


def display_help_menu(console: Console | None = None) -> None:
    """Display a beautifully categorized command manual."""
    con = console or Console()

    table = Table(
        title="Available commands:",
        header_style="bold cyan",
        border_style="dim",
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Command", style="bold green", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")

    # Grouped commands
    commands_data = [
        # Session
        ("/help", "General", "Show this categorized help manual"),
        ("/exit, /quit", "Session", "Exit the chat session"),
        ("/thread", "Session", "Show active thread ID"),
        ("/threads", "Session", "List all saved conversation threads"),
        ("/new [id]", "Session", "Start a new conversation thread"),
        ("/switch-thread <id>", "Session", "Switch to an existing thread"),
        # Model
        ("/models", "Model", "List all configured model aliases"),
        ("/switch <model>", "Model", "Switch active model on-the-fly"),
        # Memory
        ("/list-memories", "Memory", "List all long-term memory facts"),
        ("/delete-memory <id>", "Memory", "Delete a specific memory by ID"),
        ("/clear-memories", "Memory", "Wipe all long-term memories"),
        # Export & Context
        ("@<filename>", "Context", "Mention any file to inject its code into context"),
        ("/copy", "Clipboard", "Copy last assistant response to clipboard"),
        ("/export [path]", "Export", "Export full conversation history to Markdown file"),
    ]

    for cmd, cat, desc in commands_data:
        table.add_row(cmd, cat, desc)

    con.print(table)
    con.print()
