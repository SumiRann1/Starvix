from io import StringIO
from unittest.mock import Mock

from rich.console import Console

from agent_cli.ui.renderer import MarkdownStreamRenderer


def test_renderer_accumulates_and_finishes():
    out = StringIO()
    console = Console(file=out, color_system=None)
    renderer = MarkdownStreamRenderer(console=console)

    renderer.write_chunk("Hello ")
    renderer.write_chunk("**world**!")
    full = renderer.finish()

    assert full == "Hello **world**!"


def test_renderer_empty_chunk_ignored():
    renderer = MarkdownStreamRenderer()
    renderer.write_chunk("")
    assert renderer.accumulated_text == ""
    assert renderer.started is False


def test_renderer_multiple_finish_safe():
    renderer = MarkdownStreamRenderer()
    renderer.write_chunk("First chunk")
    res1 = renderer.finish()
    res2 = renderer.finish()
    assert res1 == "First chunk"
    assert res2 == "First chunk"
