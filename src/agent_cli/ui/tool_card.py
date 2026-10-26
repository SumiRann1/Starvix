from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from agent_cli.ui.theme import get_current_theme


def format_tool_input_summary(tool_input: Any) -> str:
    """Extract a concise single-line summary of tool input parameters."""
    if isinstance(tool_input, dict):
        if "cmd" in tool_input:
            return str(tool_input["cmd"])
        if "command" in tool_input:
            return str(tool_input["command"])
        if "file_path" in tool_input:
            return str(tool_input["file_path"])
        if "query" in tool_input:
            return f'"{tool_input["query"]}"'
        parts = [f"{k}={v!r}" for k, v in list(tool_input.items())[:3]]
        return ", ".join(parts)
    text = str(tool_input).strip()
    return (text[:60] + "...") if len(text) > 60 else text


def render_tool_start(
    tool_name: str,
    tool_input: Any,
    console: Console | None = None,
) -> None:
    """Render the opening execution branch for a tool invocation."""
    con = console or Console()
    theme = get_current_theme()

    summary = format_tool_input_summary(tool_input)
    text = Text()
    text.append("  ├── ⚙ ", style=f"bold {theme.tool_badge}")
    text.append(f"[{tool_name}]", style=f"bold {theme.fg}")
    if summary:
        text.append(f" {summary}", style=f"italic {theme.dim}")

    con.print(text)


def render_tool_end(
    tool_name: str,
    tool_output: Any,
    elapsed: float | None = None,
    console: Console | None = None,
) -> None:
    """Render the completed tool output with folding, truncation, and syntax highlighting."""
    con = console or Console()
    theme = get_current_theme()

    raw_str = ""
    if hasattr(tool_output, "text") and tool_output.text:
        raw_str = tool_output.text
    elif hasattr(tool_output, "content") and tool_output.content:
        raw_str = tool_output.content
    elif isinstance(tool_output, (dict, list)):
        try:
            raw_str = json.dumps(tool_output, indent=2)
        except Exception:  # noqa: BLE001
            raw_str = str(tool_output)
    else:
        raw_str = str(tool_output) if tool_output is not None else ""

    raw_str = raw_str.strip()
    is_error = any(
        err_kw in raw_str.lower()
        for err_kw in ("denied", "error", "failed", "blocked", "violation")
    )
    status_color = theme.danger if is_error else theme.success
    status_icon = "✗" if is_error else "✓"
    elapsed_str = f" [{elapsed:.2f}s]" if elapsed is not None else ""

    lines = raw_str.splitlines()
    total_lines = len(lines)

    # Header line
    header = Text()
    header.append("  └── ", style=f"dim {theme.dim}")
    header.append(f"{status_icon} ", style=f"bold {status_color}")
    header.append(f"[{tool_name}]", style=f"bold {theme.fg}")
    header.append(f"{elapsed_str}", style=f"dim {theme.dim}")

    if total_lines == 0:
        header.append(" (done)", style=f"dim {theme.dim}")
        con.print(header)
        return

    if total_lines <= 10:
        con.print(header)
        for line in lines:
            con.print(Text(f"      {line}", style=theme.dim if not is_error else theme.danger))
    else:
        # Truncate bulky outputs gracefully
        con.print(header)
        head_lines = lines[:5]
        tail_lines = lines[-3:]
        skipped = total_lines - 8

        for line in head_lines:
            con.print(Text(f"      {line}", style=theme.dim))
        con.print(Text(f"      ... [{skipped} lines folded] ...", style=f"italic {theme.accent}"))
        for line in tail_lines:
            con.print(Text(f"      {line}", style=theme.dim))


def render_hitl_approval_card(
    payload: dict | str,
    console: Console | None = None,
) -> None:
    """Render an interactive, high-contrast security approval card for Human-in-the-Loop interrupts."""
    con = console or Console()
    theme = get_current_theme()

    if isinstance(payload, dict):
        action = payload.get("action", "Action Approval")
        msg = payload.get("message", str(payload))
        file_path = payload.get("file_path")
        cmd = payload.get("cmd")
    else:
        action = "Action Approval"
        msg = str(payload)
        file_path = None
        cmd = None

    is_destructive = any(
        k in action.lower() for k in ("run_terminal", "delete", "clear", "write")
    )
    risk_level = "HIGH RISK" if is_destructive else "REVIEW REQUIRED"
    risk_style = f"bold {theme.danger}" if is_destructive else f"bold {theme.warning}"

    content = Text()
    content.append(f"⚠️  {risk_level}: ", style=risk_style)
    content.append(f"{msg}\n\n", style=f"bold {theme.fg}")

    if cmd:
        content.append("Command: ", style=f"dim {theme.dim}")
        content.append(f"{cmd}\n", style=f"bold {theme.primary}")
    if file_path:
        content.append("Target:  ", style=f"dim {theme.dim}")
        content.append(f"{file_path}\n", style=f"bold {theme.secondary}")

    content.append("\n[y] Approve   [n] Deny / Cancel", style=f"bold {theme.accent}")

    panel = Panel(
        content,
        title=f"[{risk_style}]🛡️  Security Guard & Human-in-the-Loop[/{risk_style}]",
        title_align="left",
        border_style=theme.danger if is_destructive else theme.warning,
        padding=(1, 2),
    )
    con.print()
    con.print(panel)
