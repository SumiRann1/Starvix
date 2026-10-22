from io import StringIO
from unittest.mock import Mock

from rich.console import Console

from agent_cli.ui.banner import display_help_menu, display_welcome_banner


def test_display_welcome_banner():
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)
    config = {"configurable": {"model": "test-model-42", "thread_id": "thread-abc-123"}}

    mock_tool = Mock()
    mock_tool.name = "web_search"

    display_welcome_banner(config, tools=[mock_tool], console=con)
    output = out.getvalue()

    assert "FORGE" in output
    assert "test-model-42" in output
    assert "Thread: thread-abc-123" in output
    assert "web_search" in output
    assert "/help" in output


def test_display_welcome_banner_defaults():
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)

    display_welcome_banner({}, tools=[], console=con)
    output = out.getvalue()

    assert "FORGE" in output
    assert "None" in output


def test_display_help_menu():
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)

    display_help_menu(console=con)
    output = out.getvalue()

    assert "Available commands:" in output
    assert "/help" in output
    assert "/switch" in output
    assert "/threads" in output
    assert "/copy" in output
    assert "/export" in output
