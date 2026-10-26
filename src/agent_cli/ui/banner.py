from pathlib import Path

from rich.console import Console
from rich.table import Table

from agent_cli.config import settings

# Spectre palette: steel silver body with vibrant crimson-red accent blocks
SPECTRE_FORGE = [
    r"[bold #ff374c]██[/bold #ff374c][bold #dee2e8]█████╗[/bold #dee2e8]   [bold #dee2e8]██████╗[/bold #dee2e8]   [bold #dee2e8]██████╗[/bold #dee2e8]    [bold #dee2e8]██████╗[/bold #dee2e8]   [bold #ff374c]██[/bold #ff374c][bold #dee2e8]█████╗[/bold #dee2e8]",
    r"[bold #dee2e8]██╔════╝[/bold #dee2e8]  [bold #ff374c]██[/bold #ff374c][bold #dee2e8]╔═══██╗[/bold #dee2e8]  [bold #dee2e8]██╔══██╗[/bold #dee2e8]  [bold #ff374c]██[/bold #ff374c][bold #dee2e8]╔════╝[/bold #dee2e8]   [bold #dee2e8]██╔════╝[/bold #dee2e8]",
    r"[bold #dee2e8]█████╗[/bold #dee2e8]    [bold #dee2e8]██║   ██║[/bold #dee2e8]  [bold #ff374c]██████╔╝[/bold #ff374c]  [bold #dee2e8]██║  ███╗[/bold #dee2e8]  [bold #dee2e8]█████╗[/bold #dee2e8]  ",
    r"[bold #dee2e8]██╔══╝[/bold #dee2e8]    [bold #dee2e8]██║   ██║[/bold #dee2e8]  [bold #dee2e8]██╔══██╗[/bold #dee2e8]  [bold #dee2e8]██║   ██║[/bold #dee2e8]  [bold #dee2e8]██╔══╝[/bold #dee2e8]  ",
    r"[bold #ff374c]██[/bold #ff374c][bold #dee2e8]║[/bold #dee2e8]       [bold #dee2e8]╚██████╔╝[/bold #dee2e8]  [bold #dee2e8]██║  ██║[/bold #dee2e8]  [bold #dee2e8]╚██████╔╝[/bold #dee2e8]  [bold #dee2e8]██████[/bold #dee2e8][bold #ff374c]█╗[/bold #ff374c]",
    r"[dim #848e9e]╚═╝        ╚═════╝   ╚═╝  ╚═╝   ╚═════╝   ╚══════╝[/dim #848e9e]",
]


def display_welcome_banner(
    config: dict,
    tools: list | None = None,
    console: Console | None = None,
) -> None:
    """Display the clean Spectre-styled wordmark (steel-silver with crimson-red accents)."""
    con = console or Console()

    configurable = config.get("configurable", {}) if config else {}
    current_model = configurable.get("model") or settings.current_model
    thread_id = configurable.get("thread_id", "default")
    tools_list = tools or []
    tool_names = [getattr(t, "name", str(t)) for t in tools_list]
    tools_str = (
        f"{len(tool_names)} active ({', '.join(tool_names[:3])}{'...' if len(tool_names) > 3 else ''})"
        if tool_names
        else "None"
    )

    try:
        workspace_display = str(Path.cwd().name)
    except Exception:  # noqa: BLE001
        workspace_display = "workspace"

    con.print()
    for line in SPECTRE_FORGE:
        con.print(line)
    con.print()

    # Sleek, dimmed session summary
    con.print(
        f"[dim #848e9e]FORGE • Model: [white]{current_model}[/white] • Thread: {thread_id} • "
        f"Tools: [white]{tools_str}[/white] • Workspace: [white]{workspace_display}[/white] • Type [cyan]/help[/cyan][/dim #848e9e]\n"
    )


def display_help_menu(console: Console | None = None) -> None:
    """Display a beautifully categorized command manual in the Spectre theme."""
    con = console or Console()

    table = Table(
        title="Available commands:",
        header_style="bold #ff374c",
        border_style="dim #848e9e",
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Command", style="bold #ff374c", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")

    commands_data = [
        # Session
        ("/help", "General", "Show this categorized help manual"),
        ("/exit, /quit", "Session", "Exit the chat session"),
        ("/thread", "Session", "Show active thread ID"),
        ("/threads", "Session", "List all saved conversation threads"),
        ("/new [id]", "Session", "Start a new conversation thread"),
        ("/switch-thread <id>", "Session", "Switch to an existing thread"),
        # Model & Appearance
        ("/models", "Model", "List all configured model aliases"),
        ("/switch <model>", "Model", "Switch active model on-the-fly"),
        ("/theme [name]", "Appearance", "View or switch statusbar theme (e.g. spectre, tokyo_night, catppuccin)"),
        # Memory
        ("/list-memories", "Memory", "List all long-term memory facts"),
        ("/delete-memory <id>", "Memory", "Delete a specific memory by ID"),
        ("/clear-memories", "Memory", "Wipe all long-term memories"),
        # Shell
        ("!<command>", "Shell", "Run direct terminal command without LLM (e.g. !git status)"),
        # Export & Context
        ("@<filename>", "Context", "Mention any file to inject its code into context"),
        ("/copy", "Clipboard", "Copy last assistant response to clipboard"),
        (
            "/export [path]",
            "Export",
            "Export full conversation history to Markdown file",
        ),
    ]

    for cmd, cat, desc in commands_data:
        table.add_row(cmd, cat, desc)

    con.print(table)
    con.print()
