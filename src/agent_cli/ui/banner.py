from pathlib import Path

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

from agent_cli.config import settings
from agent_cli.ui.theme import get_current_theme

# Base ASCII Wordmark template preserved for backwards compatibility
STARVIX_LOGO_RAW = [
    r"███████╗████████╗ █████╗ ██████╗ ██╗   ██╗██╗██╗  ██╗",
    r"██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║   ██║██║╚██╗██╔╝",
    r"███████╗   ██║   ███████║██████╔╝██║   ██║██║ ╚███╔╝ ",
    r"╚════██║   ██║   ██╔══██║██╔══██╗╚██╗ ██╔╝██║ ██╔██╗ ",
    r"███████║   ██║   ██║  ██║██║  ██║ ╚████╔╝ ██║██╔╝ ██╗",
    r"╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═╝  ╚═╝",
]


def display_welcome_banner(
    config: dict,
    tools: list | None = None,
    console: Console | None = None,
) -> None:
    """Display a modern, sleek developer header card inspired by Claude Code and Warp."""
    con = console or Console()
    theme = get_current_theme()

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

    # Clean display for long model strings
    model_display = current_model
    if ":" in current_model and "/" in current_model:
        prov = current_model.split(":")[0]
        slug = current_model.split("/")[-1].split(":")[0]
        if len(slug) > 20:
            slug = slug[:18] + ".."
        model_display = f"{slug} ({prov})"

    # Layout: Modern 2-column grid
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)

    left = Table.grid(padding=(0, 0))
    left.add_row(f"[bold {theme.primary}]● Model:[/bold {theme.primary}] {model_display}")
    left.add_row(f"[bold {theme.accent}]● Tools:[/bold {theme.accent}] {tools_str}")

    right = Table.grid(padding=(0, 0))
    right.add_row(f"[bold {theme.secondary}]● Thread:[/bold {theme.secondary}] {thread_id}")
    right.add_row(f"[bold {theme.tool_badge}]● Workspace:[/bold {theme.tool_badge}] {workspace_display}")

    grid.add_row(left, right)

    tip_text = (
        f"[dim {theme.dim}]Type [/dim {theme.dim}]"
        f"[bold {theme.accent}]/help[/bold {theme.accent}]"
        f"[dim {theme.dim}] for commands  •  [/dim {theme.dim}]"
        f"[bold {theme.secondary}]@file[/bold {theme.secondary}]"
        f"[dim {theme.dim}] to attach context  •  [/dim {theme.dim}]"
        f"[bold {theme.tool_badge}]!cmd[/bold {theme.tool_badge}]"
        f"[dim {theme.dim}] for direct shell[/dim {theme.dim}]"
    )

    p = theme.primary
    acc = theme.accent
    dm = theme.dim
    logo_lines = [
        f"[bold {p}]███████╗[/bold {p}][bold {acc}]████████╗[/bold {acc}] [bold {p}]█████╗[/bold {p}] [bold {acc}]██████╗[/bold {acc}] [bold {p}]██╗   ██╗[/bold {p}][bold {acc}]██╗[/bold {acc}][bold {p}]██╗  ██╗[/bold {p}]",
        f"[bold {p}]██╔════╝[/bold {p}][bold {acc}]╚══██╔══╝[/bold {acc}][bold {p}]██╔══██╗[/bold {p}][bold {acc}]██╔══██╗[/bold {acc}][bold {p}]██║   ██║[/bold {p}][bold {acc}]██║[/bold {acc}][bold {p}]╚██╗██╔╝[/bold {p}]",
        f"[bold {p}]███████╗[/bold {p}][bold {acc}]   ██║   [/bold {acc}][bold {p}]███████║[/bold {p}][bold {acc}]██████╔╝[/bold {acc}][bold {p}]██║   ██║[/bold {p}][bold {acc}]██║[/bold {acc}][bold {p}] ╚███╔╝ [/bold {p}]",
        f"[bold {p}]╚════██║[/bold {p}][bold {acc}]   ██║   [/bold {acc}][bold {p}]██╔══██║[/bold {p}][bold {acc}]██╔══██╗[/bold {acc}][bold {p}]╚██╗ ██╔╝[/bold {p}][bold {acc}]██║[/bold {acc}][bold {p}] ██╔██╗ [/bold {p}]",
        f"[bold {p}]███████║[/bold {p}][bold {acc}]   ██║   [/bold {acc}][bold {p}]██║  ██║[/bold {p}][bold {acc}]██║  ██║[/bold {acc}][bold {p}] ╚████╔╝ [/bold {p}][bold {acc}]██║[/bold {acc}][bold {p}]██╔╝ ██╗[/bold {p}]",
        f"[dim {dm}]╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═╝  ╚═╝[/dim {dm}]",
    ]

    title = f" [bold {theme.primary}]✦ STARVIX[/bold {theme.primary}] [dim {theme.dim}]│ AI Agent Runtime[/dim {theme.dim}] "

    panel = Panel(
        Group(
            grid,
            "",
            tip_text,
        ),
        title=title,
        title_align="left",
        border_style=theme.panel_border,
        box=ROUNDED,
        padding=(1, 2),
    )

    aligned_logo = Align.center(Group(*[con.render_str(l) for l in logo_lines]))

    con.print()
    con.print(aligned_logo)
    con.print()
    con.print(panel)
    con.print()


def display_help_menu(console: Console | None = None) -> None:
    """Display a beautifully categorized command manual matching the active theme."""
    con = console or Console()
    theme = get_current_theme()

    table = Table(
        title="Available commands:",
        header_style=f"bold {theme.primary}",
        border_style=theme.panel_border,
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Command", style=f"bold {theme.primary}", no_wrap=True)
    table.add_column("Category", style=theme.accent)
    table.add_column("Description", style=theme.fg)

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
        (
            "/theme [name]",
            "Appearance",
            "View or switch statusbar theme (e.g. tokyo_night, catppuccin, dracula, monokai)",
        ),
        # Memory
        ("/list-memories", "Memory", "List all long-term memory facts"),
        ("/delete-memory <id>", "Memory", "Delete a specific memory by ID"),
        ("/clear-memories", "Memory", "Wipe all long-term memories"),
        # Shell & Utility
        ("!<command>", "Shell", "Run direct terminal command without LLM (e.g. !git status)"),
        ("/clear", "Screen", "Clear terminal screen and re-render header"),
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

