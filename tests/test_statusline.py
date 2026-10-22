from unittest.mock import Mock, patch

from prompt_toolkit.formatted_text import HTML

from agent_cli.config import StatusbarConfig
from agent_cli.ui.statusline import get_statusline, resolve_statusbar_colors


def test_get_statusline_defaults():
    config = {"configurable": {"model": "groq:openai/gpt-oss-20b", "thread_id": "session-12345"}}
    result = get_statusline(config)
    assert isinstance(result, HTML)
    html_str = result.value
    assert "gpt-oss-20b" in html_str
    assert "session-12345" in html_str
    assert "Memories:</b>" in html_str
    assert ">0</style>" in html_str


def test_get_statusline_with_memories():
    mock_store = Mock()
    mock_store.search.return_value = ["item1", "item2", "item3"]
    config = {"configurable": {"model": "openrouter:nvidia/nemotron-3-ultra-550b", "thread_id": "session-long-id-12345678"}}
    result = get_statusline(config, store=mock_store)
    html_str = result.value
    assert "Memories:</b>" in html_str
    assert ">3</style>" in html_str
    assert "nemotron-3-ultra" in html_str


def test_get_statusline_empty_config():
    result = get_statusline({})
    assert isinstance(result, HTML)
    assert "Memories:" in result.value


def test_resolve_statusbar_colors_preset():
    sb = StatusbarConfig(theme="dracula")
    colors = resolve_statusbar_colors(sb)
    assert colors["bg"] == "#282a36"
    assert colors["model_color"] == "#50fa7b"
    assert colors["thread_color"] == "#8be9fd"


def test_resolve_statusbar_colors_custom_override():
    sb = StatusbarConfig(theme="nord", bg="#111111", model_color="#ff0000")
    colors = resolve_statusbar_colors(sb)
    assert colors["bg"] == "#111111"
    assert colors["model_color"] == "#ff0000"
    # Non-overridden colors stay from the preset
    assert colors["thread_color"] == "#88c0d0"


def test_get_statusline_with_custom_settings():
    custom_sb = StatusbarConfig(theme="custom", bg="#abcdef", fg="#123456")
    with patch("agent_cli.ui.statusline.settings.statusbar", custom_sb):
        result = get_statusline({})
        assert 'bg="#abcdef"' in result.value
        assert 'fg="#123456"' in result.value
