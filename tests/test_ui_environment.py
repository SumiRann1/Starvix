import os
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from agent_cli.config import set_theme, settings
from agent_cli.ui.animation import play_startup_animation, render_logo
from agent_cli.ui.completer import ChatBotCompleter
from agent_cli.ui.statusline import THEMES


def test_render_logo():
    logo = render_logo(0)
    assert "FORGE" in logo.plain or "███████" in logo.plain


def test_play_startup_animation_non_tty():
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)

    # In test / non-tty environments, it should gracefully and instantly return
    play_startup_animation(console=con, speed=10.0, tools_count=5)
    # Shouldn't raise any errors


def test_play_startup_animation_disabled_via_env(monkeypatch):
    monkeypatch.setenv("FORGE_NO_ANIMATION", "1")
    out = StringIO()
    con = Console(file=out, color_system=None, width=120)
    play_startup_animation(console=con, speed=10.0, tools_count=5)


def test_set_theme_valid():
    original_theme = settings.statusbar.theme
    try:
        assert set_theme("dracula") is True
        assert settings.statusbar.theme == "dracula"
        assert set_theme("catppuccin") is True
        assert settings.statusbar.theme == "catppuccin"
    finally:
        set_theme(original_theme)


def test_set_theme_invalid():
    with pytest.raises(ValueError, match="not found"):
        set_theme("non_existent_theme_xyz")


def test_completer_theme_suggestions():
    completer = ChatBotCompleter()
    doc = Mock()
    doc.text_before_cursor = "/theme "
    completions = list(completer.get_completions(doc, None))
    theme_texts = [c.text for c in completions]

    assert "catppuccin" in theme_texts
    assert "tokyo_night" in theme_texts
    assert "dracula" in theme_texts


def test_direct_shell_execution():
    from agent_cli.chat import _execute_direct_shell

    out = StringIO()
    con = Console(file=out, color_system=None, width=120)

    _execute_direct_shell("echo 'forge-terminal-test'", console=con)
    output = out.getvalue()
    assert "forge-terminal-test" in output
    assert "Shell:" in output
