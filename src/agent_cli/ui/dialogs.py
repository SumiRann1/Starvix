from __future__ import annotations

import os
from typing import Any

from rich.console import Console
from rich.table import Table

from agent_cli.config import settings
from agent_cli.ui.theme import THEME_REGISTRY, get_current_theme


def render_models_table(
    current_model: str,
    console: Console | None = None,
) -> None:
    """Render configured models in a styled Rich Table."""
    con = console or Console()
    theme = get_current_theme()

    table = Table(
        title="🤖 Configured AI Models",
        title_style=f"bold {theme.primary}",
        border_style=theme.panel_border,
        header_style=f"bold {theme.primary}",
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Alias", style=f"bold {theme.fg}", no_wrap=True)
    table.add_column("Provider", style=theme.accent)
    table.add_column("Model Identifier", style=theme.dim)
    table.add_column("Status", style=f"bold {theme.success}", justify="center")

    for key, val in settings.models.items():
        is_current = (key == current_model or val == current_model)
        provider = val.split(":")[0] if ":" in val else "custom"
        status_text = "● Active" if is_current else "○"
        status_style = f"bold {theme.success}" if is_current else theme.dim

        table.add_row(
            key,
            provider,
            val,
            f"[{status_style}]{status_text}[/{status_style}]",
        )

    con.print()
    con.print(table)
    con.print(f"[dim {theme.dim}]Switch model on-the-fly: [bold {theme.accent}]/switch <alias>[/bold {theme.accent}][/dim {theme.dim}]\n")


def render_threads_table(
    threads: list[str],
    current_thread: str,
    console: Console | None = None,
) -> None:
    """Render saved conversation threads in a styled Rich Table."""
    con = console or Console()
    theme = get_current_theme()

    table = Table(
        title="🧵 Conversation Threads",
        title_style=f"bold {theme.primary}",
        border_style=theme.panel_border,
        header_style=f"bold {theme.primary}",
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Thread ID", style=f"bold {theme.fg}", no_wrap=True)
    table.add_column("Status", style=f"bold {theme.success}", justify="center")

    if not threads:
        table.add_row("(No saved threads found)", "")
    else:
        for tid in threads:
            is_active = tid == current_thread
            status = "● Current" if is_active else "○"
            status_style = f"bold {theme.success}" if is_active else theme.dim
            table.add_row(tid, f"[{status_style}]{status}[/{status_style}]")

    if current_thread != "-" and current_thread not in threads:
        table.add_row(
            f"{current_thread} [italic](unsaved session)[/italic]",
            f"[bold {theme.success}]● Current[/bold {theme.success}]",
        )

    con.print()
    con.print(table)
    con.print(f"[dim {theme.dim}]Switch thread: [bold {theme.accent}]/switch-thread <id>[/bold {theme.accent}] • New: [bold {theme.accent}]/new[/bold {theme.accent}][/dim {theme.dim}]\n")


def render_memories_table(
    memories: list[Any],
    console: Console | None = None,
) -> None:
    """Render long-term memory facts in a styled Rich Table."""
    con = console or Console()
    theme = get_current_theme()

    table = Table(
        title="🧠 Long-Term Memory (LTM)",
        title_style=f"bold {theme.primary}",
        border_style=theme.panel_border,
        header_style=f"bold {theme.primary}",
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Memory Fact", style=theme.fg)

    if not memories:
        table.add_row(f"[dim {theme.dim}](No memories stored yet. Starvix learns facts during conversation.)[/dim {theme.dim}]")

    else:
        for mem in memories:
            table.add_row(str(mem))

    con.print()
    con.print(table)
    con.print(f"[dim {theme.dim}]Manage memories: [bold {theme.accent}]/delete-memory <id>[/bold {theme.accent}] • [bold {theme.accent}]/clear-memories[/bold {theme.accent}][/dim {theme.dim}]\n")


def render_themes_table(
    current_theme_name: str,
    console: Console | None = None,
) -> None:
    """Render available designer themes with color previews in a styled Rich Table."""
    con = console or Console()
    active_theme = get_current_theme()

    table = Table(
        title="🎨 Available TUI Designer Themes",
        title_style=f"bold {active_theme.primary}",
        border_style=active_theme.panel_border,
        header_style=f"bold {active_theme.primary}",
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("Theme", style=f"bold {active_theme.fg}", no_wrap=True)
    table.add_column("Accent", justify="center")
    table.add_column("Background", justify="center")
    table.add_column("Palette Style", style=active_theme.dim)
    table.add_column("Status", justify="center")

    theme_descriptions = {
        "tokyo_night": "Deep slate blue with violet & cyan",
        "catppuccin": "Pastel mocha cozy aesthetic",
        "dracula": "High-contrast purple, pink & neon green",
        "nord": "Arctic frost minimalist tones",
        "monokai": "Warm developer hacker classic",
        "cyberpunk": "Vibrant neon cyan, yellow & magenta",
        "spectre": "Steel silver with crimson accents",
        "matrix": "Hacker terminal monochrome green",
        "minimal": "Monochrome dark gray and crisp white",
        "strands": "Clean mint-green borderless style",
    }

    for name, palette in THEME_REGISTRY.items():
        is_active = name == current_theme_name
        status = "● Active" if is_active else "○"
        status_style = f"bold {active_theme.success}" if is_active else active_theme.dim

        accent_sample = f"[{palette.primary}]████[/{palette.primary}]"
        bg_sample = f"[{palette.bg}]████[/{palette.bg}]"
        desc = theme_descriptions.get(name, "Custom palette")

        table.add_row(
            name,
            accent_sample,
            bg_sample,
            desc,
            f"[{status_style}]{status}[/{status_style}]",
        )

    con.print()
    con.print(table)
    con.print(f"[dim {active_theme.dim}]Switch theme on-the-fly: [bold {active_theme.accent}]/theme <name>[/bold {active_theme.accent}][/dim {active_theme.dim}]\n")


def clear_screen(
    config: dict | None = None,
    tools: list | None = None,
    console: Console | None = None,
) -> None:
    """Clear terminal screen and re-render header cleanly."""
    con = console or Console()
    # Cross-platform screen clear
    os.system("cls" if os.name == "nt" else "clear")

    from agent_cli.ui.banner import display_welcome_banner

    if config is not None:
        display_welcome_banner(config, tools=tools, console=con)
