from __future__ import annotations

import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent_cli.ui.theme import get_current_theme


def render_user_message(query: str, attached_files: list[str] | None = None, console: Console | None = None) -> None:
    """Render the user prompt in a crisp, framed card with timestamp and file attachments."""
    con = console or Console()
    theme = get_current_theme()
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    title = Text()
    title.append("  You ", style=f"bold {theme.primary}")
    title.append(f"[{timestamp}] ", style=f"dim {theme.dim}")

    content = Text(query, style=theme.fg)
    if attached_files:
        content.append("\n\n")
        content.append("📎 Context: ", style=f"bold {theme.secondary}")
        for idx, f in enumerate(attached_files):
            sep = " • " if idx > 0 else ""
            content.append(f"{sep}@{Path(f).name}", style=f"italic {theme.accent}")

    panel = Panel(content, title=title, title_align="left", border_style=theme.panel_border, padding=(0, 1))
    con.print()
    con.print(panel)


def render_assistant_header(model_name: str, console: Console | None = None) -> None:
    """Render the assistant starting delimiter."""
    con = console or Console()
    theme = get_current_theme()

    display_name = model_name.split("/")[-1].split(":")[-1] if model_name else "Starvix"

    header = Text()
    header.append("╭─ 🤖 ", style=f"bold {theme.primary}")
    header.append(f"{display_name} ", style=f"bold {theme.fg}")
    header.append("─" * 40, style=f"dim {theme.panel_border}")

    con.print()
    con.print(header)


def render_assistant_footer(
    console: Console | None = None,
) -> None:
    """Render the bottom closing border for the assistant response."""
    con = console or Console()
    theme = get_current_theme()
    con.print(Text("╰" + "─" * 60, style=f"dim {theme.panel_border}"))


def render_telemetry_badge(
    model: str,
    provider: str = "",
    prompt_tokens: int | str = "-",
    completion_tokens: int | str = "-",
    total_tokens: int | str = "-",
    tok_per_sec: float | None = None,
    elapsed_seconds: float | None = None,
    finish_reason: str = "stop",
    console: Console | None = None,
) -> None:
    """Render high-performance generation telemetry and token counts in a clean bar."""
    con = console or Console()
    theme = get_current_theme()

    short_model = model.split("/")[-1] if "/" in model else model
    provider_str = f" ({provider})" if provider else ""

    text = Text()
    text.append("  ⚡ ", style=f"bold {theme.primary}")
    text.append(f"{short_model}{provider_str}", style=theme.fg)
    text.append(" • ", style=f"dim {theme.dim}")

    if tok_per_sec is not None and tok_per_sec > 0:
        text.append(f"{tok_per_sec:.1f} tok/s", style=f"bold {theme.success}")
        text.append(" • ", style=f"dim {theme.dim}")

    if elapsed_seconds is not None:
        text.append(f"{elapsed_seconds:.2f}s", style=f"{theme.dim}")
        text.append(" • ", style=f"dim {theme.dim}")

    text.append(f"tokens: {completion_tokens} out / {total_tokens} total", style=f"dim {theme.dim}")
    if finish_reason and finish_reason != "completed":
        text.append(f" • finish: {finish_reason}", style=f"dim {theme.dim}")

    con.print(text)
    con.print()


def render_graph_step(
    node_name: str,
    status: str = "running",
    elapsed: float | None = None,
    console: Console | None = None,
) -> None:
    """Render LangGraph node execution transitions with subtle tree styling."""
    con = console or Console()
    theme = get_current_theme()

    text = Text()
    if status == "running":
        text.append("  ├── ⚡ ", style=f"dim {theme.dim}")
        text.append(f"[{node_name}]", style=f"bold {theme.accent}")
        text.append(" executing...", style=f"dim {theme.dim}")
    elif status == "completed":
        elapsed_str = f" in {elapsed:.2f}s" if elapsed is not None else ""
        text.append("  └── ✓ ", style=f"bold {theme.success}")
        text.append(f"[{node_name}]", style=f"dim {theme.fg}")
        text.append(f" done{elapsed_str}", style=f"dim {theme.dim}")
    con.print(text)
