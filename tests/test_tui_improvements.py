from io import StringIO
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from agent_cli.chat import _handle_command
from agent_cli.config import StatusbarConfig
from agent_cli.ui.dialogs import (
    clear_screen,
    render_memories_table,
    render_models_table,
    render_themes_table,
    render_threads_table,
)
from agent_cli.ui.message_frame import (
    render_assistant_footer,
    render_assistant_header,
    render_graph_step,
    render_telemetry_badge,
    render_user_message,
)
from agent_cli.ui.renderer import MarkdownStreamRenderer
from agent_cli.ui.theme import THEME_REGISTRY, get_current_theme
from agent_cli.ui.tool_card import (
    format_tool_input_summary,
    render_hitl_approval_card,
    render_tool_end,
    render_tool_start,
)


def test_theme_registry_all_themes_complete():
    """Verify that all designer themes define complete palette tokens."""
    expected_themes = [
        "strands",
        "tokyo_night",
        "catppuccin",
        "dracula",
        "nord",
        "monokai",
        "cyberpunk",
        "spectre",
        "matrix",
        "minimal",
    ]
    for name in expected_themes:
        assert name in THEME_REGISTRY
        palette = THEME_REGISTRY[name]
        assert palette.primary.startswith("#")
        assert palette.bg.startswith("#")
        assert palette.fg.startswith("#")
        assert palette.panel_border.startswith("#")
        assert palette.code_theme


def test_get_current_theme_overrides():
    """Verify that explicit StatusbarConfig overrides apply cleanly."""
    sb = StatusbarConfig(theme="catppuccin", bg="#001122", model_color="#ff5555")
    theme = get_current_theme(sb)
    assert theme.name == "catppuccin"
    assert theme.bg == "#001122"
    assert theme.primary == "#ff5555"


def test_markdown_renderer_cot_thinking_extraction():
    """Verify that <think>...</think> tags are cleanly extracted from final display text."""
    out = StringIO()
    console = Console(file=out, color_system=None)
    renderer = MarkdownStreamRenderer(console=console)

    renderer.write_chunk("Intro: ")
    renderer.write_chunk("<think>Checking facts and formulating answer</think>")
    renderer.write_chunk("Here is the answer.")
    res = renderer.finish()

    assert "Intro: " in res
    assert "Here is the answer." in res
    assert "<think>" in res
    # Verify display text strips <think>
    display_clean = renderer._get_display_text()
    assert "<think>" not in display_clean
    assert "</think>" not in display_clean
    assert "Checking facts" not in display_clean
    assert "Here is the answer." in display_clean


def test_render_user_message():
    """Verify user message framing card."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=100)
    render_user_message("Refactor the parser", attached_files=["src/main.py"], console=con)
    rendered = out.getvalue()
    assert "You" in rendered
    assert "Refactor the parser" in rendered
    assert "@main.py" in rendered


def test_render_assistant_header_and_footer():
    """Verify assistant container delimiters."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=100)
    render_assistant_header("groq:openai/gpt-oss-120b", console=con)
    render_assistant_footer(console=con)
    rendered = out.getvalue()
    assert "gpt-oss-120b" in rendered
    assert "─" in rendered


def test_render_telemetry_badge():
    """Verify generation performance bar."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)
    render_telemetry_badge(
        model="openrouter:nvidia/nemotron",
        provider="openrouter",
        prompt_tokens=150,
        completion_tokens=85,
        total_tokens=235,
        tok_per_sec=42.5,
        elapsed_seconds=2.0,
        console=con,
    )
    rendered = out.getvalue()
    assert "nemotron" in rendered
    assert "42.5 tok/s" in rendered
    assert "85 out" in rendered


def test_render_graph_step():
    """Verify LangGraph node transition steps."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=100)
    render_graph_step("tools_node", status="running", console=con)
    render_graph_step("tools_node", status="completed", elapsed=0.45, console=con)
    rendered = out.getvalue()
    assert "tools_node" in rendered
    assert "executing" in rendered
    assert "done" in rendered
    assert "0.45s" in rendered


def test_tool_start_and_end_short():
    """Verify short tool output execution rendering."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=100)
    render_tool_start("read_file", {"file_path": "test.txt"}, console=con)
    render_tool_end("read_file", "File contents here", elapsed=0.05, console=con)
    rendered = out.getvalue()
    assert "read_file" in rendered
    assert "test.txt" in rendered
    assert "File contents here" in rendered
    assert "0.05s" in rendered


def test_tool_end_folded_output():
    """Verify bulky tool outputs are gracefully folded."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=100)
    long_output = "\n".join([f"Line {i}" for i in range(25)])
    render_tool_end("run_terminal_cmd", long_output, elapsed=1.2, console=con)
    rendered = out.getvalue()
    assert "Line 0" in rendered
    assert "Line 24" in rendered
    assert "lines folded" in rendered


def test_tool_end_error_highlighting():
    """Verify error detection in tool output."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=100)
    render_tool_end("execute", "Access Denied by Guardrails", console=con)
    rendered = out.getvalue()
    assert "✗" in rendered
    assert "Access Denied by Guardrails" in rendered


def test_render_hitl_approval_card():
    """Verify interactive security approval card."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=100)
    payload = {
        "action": "run_terminal_cmd",
        "cmd": "rm -rf build/",
        "message": "Remove build cache directory?",
    }
    render_hitl_approval_card(payload, console=con)
    rendered = out.getvalue()
    assert "HIGH RISK" in rendered
    assert "rm -rf build/" in rendered
    assert "Remove build cache" in rendered
    assert "[y] Approve" in rendered


def test_dialogs_tables():
    """Verify slash command rich tables for models, threads, memories, themes."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)

    render_models_table("groq:openai/gpt-oss-20b", console=con)
    render_threads_table(["session-1", "session-2"], "session-1", console=con)
    render_memories_table(["User prefers python", "Target is Linux"], console=con)
    render_themes_table("tokyo_night", console=con)

    rendered = out.getvalue()
    assert "Configured AI Models" in rendered
    assert "Conversation Threads" in rendered
    assert "Long-Term Memory" in rendered
    assert "Available TUI Designer Themes" in rendered
    assert "session-1" in rendered
    assert "User prefers python" in rendered


def test_handle_command_clear(capsys):
    """Verify /clear slash command clears screen and returns True."""
    config = {"configurable": {"model": "test", "thread_id": "session-123"}}
    with patch("os.system") as mock_sys:
        handled = _handle_command("/clear", config)
        assert handled is True
        mock_sys.assert_called_once()


def test_handle_command_theme_list():
    """Verify /theme renders the rich themes table."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)
    config = {"configurable": {"model": "test"}}
    handled = _handle_command("/theme", config, console=con)
    assert handled is True
    rendered = out.getvalue()
    assert "Available TUI Designer Themes" in rendered
    assert "catppuccin" in rendered
    assert "tokyo_night" in rendered
    assert "dracula" in rendered


def test_handle_command_theme_switch():
    """Verify /theme <name> updates settings and updates session style."""
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)
    mock_session = Mock()
    config = {"configurable": {"model": "test"}}
    handled = _handle_command(
        "/theme catppuccin",
        config,
        session=mock_session,
        console=con,
    )
    assert handled is True
    rendered = out.getvalue()
    assert "Switched statusbar theme to: catppuccin" in rendered
    assert "Available TUI Designer Themes" in rendered
    assert mock_session.style is not None

