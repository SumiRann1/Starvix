from unittest.mock import Mock, patch

import pytest

from agent_cli.chat import _extract_chunk_text, _handle_command, main


class DummyChunk:
    def __init__(self, text=None, content=None):
        if text is not None:
            self.text = text
        if content is not None:
            self.content = content


def test_extract_chunk_text_none_and_empty():
    assert _extract_chunk_text(None) == ""
    assert _extract_chunk_text("") == ""
    assert _extract_chunk_text(DummyChunk()) == ""


def test_extract_chunk_text_with_text_attr():
    chunk = DummyChunk(text="Hello from text attr")
    assert _extract_chunk_text(chunk) == "Hello from text attr"


def test_extract_chunk_text_string_content():
    chunk = DummyChunk(content="Hello from content")
    assert _extract_chunk_text(chunk) == "Hello from content"


def test_extract_chunk_text_list_of_strings():
    chunk = DummyChunk(content=["Hello", " ", "world!"])
    assert _extract_chunk_text(chunk) == "Hello world!"


def test_extract_chunk_text_list_of_dicts():
    chunk = DummyChunk(
        content=[
            {"type": "text", "text": "Part 1"},
            {"text": " Part 2"},
            {"type": "other", "value": 123},  # ignored
            " trailing",
        ]
    )
    assert _extract_chunk_text(chunk) == "Part 1 Part 2 trailing"


def test_extract_chunk_text_unsupported_content_type():
    chunk = DummyChunk(content=12345)
    assert _extract_chunk_text(chunk) == ""


def test_handle_command_help(capsys):
    config = {"configurable": {"model": "test"}}
    handled = _handle_command("/help", config)
    assert handled is True
    captured = capsys.readouterr()
    assert "/help" in captured.out
    assert "/switch" in captured.out


def test_handle_command_models(capsys):
    config = {"configurable": {"model": "test"}}
    with (
        patch("agent_cli.chat.settings.models", {"model_1": "provider:m1", "model_2": "provider:m2"}),
        patch("agent_cli.chat.settings.current_model", "provider:m1"),
    ):
        handled = _handle_command("/models", config)
        assert handled is True
        captured = capsys.readouterr()
        assert "model_1" in captured.out
        assert "model_2" in captured.out
        assert "(current)" in captured.out


def test_handle_command_switch_missing_args(capsys):
    config = {"configurable": {"model": "test"}}
    handled = _handle_command("/switch", config)
    assert handled is True
    captured = capsys.readouterr()
    assert "Usage: /switch <model_name>" in captured.out


def test_handle_command_switch_valid(capsys):
    config = {"configurable": {"model": "old-model"}}
    with patch("agent_cli.chat.settings.models", {"new_model": "provider:new-model"}):
        handled = _handle_command("/switch new_model", config)
        assert handled is True
        assert config["configurable"]["model"] == "provider:new-model"
        captured = capsys.readouterr()
        assert "Switched to model" in captured.out


def test_handle_command_switch_invalid(capsys):
    config = {"configurable": {"model": "old-model"}}
    handled = _handle_command("/switch non_existent_model", config)
    assert handled is True
    assert config["configurable"]["model"] == "old-model"
    captured = capsys.readouterr()
    assert "Error: Model 'non_existent_model' not found." in captured.out


def test_handle_command_exit():
    config = {"configurable": {"model": "test"}}
    assert _handle_command("/exit", config) is False
    assert _handle_command("/quit", config) is False


def test_handle_command_unknown(capsys):
    config = {"configurable": {"model": "test"}}
    handled = _handle_command("/foobar", config)
    assert handled is True
    captured = capsys.readouterr()
    assert "Unknown command '/foobar'" in captured.out


@pytest.mark.anyio
async def test_main_exits_on_eof(capsys):
    with (
        patch("builtins.input", side_effect=EOFError),
        patch("agent_cli.chat.build_graph"),
    ):
        await main()
    captured = capsys.readouterr()
    assert "Exiting chat..." in captured.out


@pytest.mark.anyio
async def test_main_exits_on_exit_command(capsys):
    with (
        patch("builtins.input", side_effect=["", "exit"]),
        patch("agent_cli.chat.build_graph"),
    ):
        await main()
    captured = capsys.readouterr()
    assert "Goodbye!" in captured.out


@pytest.mark.anyio
async def test_main_handles_slash_command_and_exits(capsys):
    with (
        patch("builtins.input", side_effect=["/help", "quit"]),
        patch("agent_cli.chat.build_graph"),
    ):
        await main()
    captured = capsys.readouterr()
    assert "Available commands:" in captured.out


@pytest.mark.anyio
async def test_main_executes_streaming_events(capsys):
    async def fake_stream(*args, **kwargs):
        yield {"event": "on_chain_start", "name": "LangGraph", "metadata": {}, "data": {}}
        yield {"event": "on_chain_start", "name": "chat", "metadata": {}, "data": {}}
        yield {
            "event": "on_chat_model_start",
            "metadata": {"ls_model_name": "test-llm", "ls_provider": "google", "ls_temperature": 0.7},
            "data": {},
        }
        yield {"event": "on_chat_model_stream", "data": {"chunk": DummyChunk(content="Hello streaming!")}}
        yield {
            "event": "on_chat_model_end",
            "data": {
                "output": Mock(
                    usage_metadata={"input_tokens": 5, "output_tokens": 10, "total_tokens": 15},
                    response_metadata={"finish_reason": "stop"},
                )
            },
        }
        yield {"event": "on_tool_start", "name": "tavily_search", "data": {"input": "weather query"}}
        yield {"event": "on_tool_end", "name": "tavily_search", "data": {"output": Mock(text="sunny")}}
        yield {"event": "on_chain_end", "name": "chat", "data": {}}
        yield {"event": "on_chain_end", "name": "LangGraph", "data": {}}

    mock_graph = Mock()
    mock_graph.astream_events = fake_stream

    with (
        patch("builtins.input", side_effect=["What's the weather?", "exit"]),
        patch("agent_cli.chat.build_graph", return_value=mock_graph),
    ):
        await main()

    captured = capsys.readouterr()
    assert "Hello streaming!" in captured.out
    assert "[Model Stats]" in captured.out
    assert "tavily_search" in captured.out
    assert "weather query" in captured.out
