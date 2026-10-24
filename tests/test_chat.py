import sqlite3
from unittest.mock import Mock, patch

import pytest

from agent_cli.chat import _extract_chunk_text, _handle_command, get_all_threads, main


class DummyChunk:
    def __init__(self, text=None, content=None):
        if text is not None:
            self.text = text
        if content is not None:
            self.content = content


def test_get_all_threads_nonexistent_file(tmp_path):
    assert get_all_threads(tmp_path / "does_not_exist.sqlite") == []


def test_get_all_threads_no_table(tmp_path):
    db_file = tmp_path / "empty.sqlite"
    with sqlite3.connect(db_file) as conn:
        conn.execute("CREATE TABLE other_table (id INT);")
    assert get_all_threads(db_file) == []


def test_get_all_threads_with_data(tmp_path):
    db_file = tmp_path / "valid.sqlite"
    with sqlite3.connect(db_file) as conn:
        conn.execute("CREATE TABLE checkpoints (thread_id TEXT NOT NULL);")
        conn.execute("INSERT INTO checkpoints VALUES ('thread-b');")
        conn.execute("INSERT INTO checkpoints VALUES ('thread-a');")
        conn.execute("INSERT INTO checkpoints VALUES ('thread-b');")
        conn.execute("INSERT INTO checkpoints VALUES ('');")
    threads = get_all_threads(db_file)
    assert threads == ["thread-a", "thread-b"]


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
    assert "/threads" in captured.out


def test_handle_command_models(capsys):
    config = {"configurable": {"model": "test"}}
    with (
        patch(
            "agent_cli.chat.settings.models",
            {"model_1": "provider:m1", "model_2": "provider:m2"},
        ),
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


def test_handle_command_thread(capsys):
    config = {"configurable": {"thread_id": "my-active-thread"}}
    handled = _handle_command("/thread", config)
    assert handled is True
    captured = capsys.readouterr()
    assert "my-active-thread" in captured.out


def test_handle_command_threads_empty(capsys):
    config = {"configurable": {"thread_id": "temp-thread"}}
    with patch("agent_cli.chat.get_all_threads", return_value=[]):
        handled = _handle_command("/threads", config)
        assert handled is True
        captured = capsys.readouterr()
        assert "(No saved threads found)" in captured.out
        assert "Current unsaved session:" in captured.out
        assert "temp-thread" in captured.out


def test_handle_command_threads_with_active_saved(capsys):
    config = {"configurable": {"thread_id": "thread-2"}}
    with patch("agent_cli.chat.get_all_threads", return_value=["thread-1", "thread-2"]):
        handled = _handle_command("/threads", config)
        assert handled is True
        captured = capsys.readouterr()
        assert "thread-1" in captured.out
        assert "thread-2" in captured.out
        assert "(current)" in captured.out


def test_handle_command_threads_with_active_unsaved(capsys):
    config = {"configurable": {"thread_id": "unsaved-thread"}}
    with patch("agent_cli.chat.get_all_threads", return_value=["thread-1"]):
        handled = _handle_command("/threads", config)
        assert handled is True
        captured = capsys.readouterr()
        assert "thread-1" in captured.out
        assert "Current unsaved session:" in captured.out
        assert "unsaved-thread" in captured.out


def test_handle_command_all_threads_alias(capsys):
    config = {"configurable": {"thread_id": "thread-1"}}
    with patch("agent_cli.chat.get_all_threads", return_value=["thread-1"]):
        handled = _handle_command("/all-threads", config)
        assert handled is True
        captured = capsys.readouterr()
        assert "thread-1" in captured.out
        assert "(current)" in captured.out


def test_handle_command_new_default(capsys):
    config = {"configurable": {"thread_id": "old-thread"}}
    handled = _handle_command("/new", config)
    assert handled is True
    assert config["configurable"]["thread_id"].startswith("session-")
    assert config["configurable"]["thread_id"] != "old-thread"
    captured = capsys.readouterr()
    assert "Started new thread" in captured.out


def test_handle_command_new_named(capsys):
    config = {"configurable": {"thread_id": "old-thread"}}
    handled = _handle_command("/new custom-named-thread", config)
    assert handled is True
    assert config["configurable"]["thread_id"] == "custom-named-thread"
    captured = capsys.readouterr()
    assert "Started new thread" in captured.out
    assert "custom-named-thread" in captured.out


def test_handle_command_switch_thread(capsys):
    config = {"configurable": {"thread_id": "thread-a"}}
    handled = _handle_command("/switch-thread thread-b", config)
    assert handled is True
    assert config["configurable"]["thread_id"] == "thread-b"
    captured = capsys.readouterr()
    assert "Switched to thread" in captured.out
    assert "thread-b" in captured.out


def test_handle_command_switch_thread_missing_arg(capsys):
    config = {"configurable": {"thread_id": "thread-a"}}
    handled = _handle_command("/switch-thread", config)
    assert handled is True
    assert config["configurable"]["thread_id"] == "thread-a"
    captured = capsys.readouterr()
    assert "Usage: /switch-thread <thread_id>" in captured.out


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
    assert "Thread:" in captured.out
    assert "session-" in captured.out


@pytest.mark.anyio
async def test_main_with_custom_thread(capsys):
    with (
        patch("builtins.input", side_effect=EOFError),
        patch("agent_cli.chat.build_graph"),
    ):
        await main(thread_id="custom-thread-999")
    captured = capsys.readouterr()
    assert "Thread:" in captured.out
    assert "custom-thread-999" in captured.out


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
        yield {
            "event": "on_chain_start",
            "name": "LangGraph",
            "metadata": {},
            "data": {},
        }
        yield {"event": "on_chain_start", "name": "chat", "metadata": {}, "data": {}}
        yield {
            "event": "on_chat_model_start",
            "metadata": {
                "ls_model_name": "test-llm",
                "ls_provider": "google",
                "ls_temperature": 0.7,
            },
            "data": {},
        }
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": DummyChunk(content="Hello streaming!")},
        }
        yield {
            "event": "on_chat_model_end",
            "data": {
                "output": Mock(
                    usage_metadata={
                        "input_tokens": 5,
                        "output_tokens": 10,
                        "total_tokens": 15,
                    },
                    response_metadata={"finish_reason": "stop"},
                )
            },
        }
        yield {
            "event": "on_tool_start",
            "name": "tavily_search",
            "data": {"input": "weather query"},
        }
        yield {
            "event": "on_tool_end",
            "name": "tavily_search",
            "data": {"output": Mock(text="sunny")},
        }
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


def test_handle_command_list_memories(capsys):
    config = {"configurable": {"thread_id": "test"}}
    mock_store = Mock()
    with patch("agent_cli.chat.get_all_memories", return_value=["[id1] Likes apples"]):
        handled = _handle_command("/list-memories", config, store=mock_store)
        assert handled is True
        captured = capsys.readouterr()
        assert "Memories:" in captured.out
        assert "[id1] Likes apples" in captured.out


def test_handle_command_clear_memories(capsys):
    config = {"configurable": {"thread_id": "test"}}
    mock_store = Mock()
    with patch("agent_cli.chat.clear_memories") as mock_clear:
        handled = _handle_command("/clear-memories", config, store=mock_store)
        assert handled is True
        mock_clear.assert_called_once_with(mock_store)
        captured = capsys.readouterr()
        assert "Cleared all memories" in captured.out


def test_handle_command_delete_memory(capsys):
    config = {"configurable": {"thread_id": "test"}}
    mock_store = Mock()
    with patch("agent_cli.chat.delete_memory") as mock_del:
        handled = _handle_command("/delete-memory mem-123", config, store=mock_store)
        assert handled is True
        mock_del.assert_called_once_with("mem-123", mock_store)
        captured = capsys.readouterr()
        assert "Deleted memory" in captured.out
        assert "mem-123" in captured.out


def test_handle_command_list_memories_empty(capsys):
    config = {"configurable": {"thread_id": "test"}}
    mock_store = Mock()
    with patch("agent_cli.chat.get_all_memories", return_value=[]):
        handled = _handle_command("/list-memories", config, store=mock_store)
        assert handled is True
        captured = capsys.readouterr()
        assert "(No memories found)" in captured.out


def test_handle_command_delete_memory_missing_id(capsys):
    config = {"configurable": {"thread_id": "test"}}
    mock_store = Mock()
    handled = _handle_command("/delete-memory", config, store=mock_store)
    assert handled is True
    captured = capsys.readouterr()
    assert "Usage: /delete-memory <memory_id>" in captured.out


def test_get_all_threads_handles_sqlite_error(tmp_path):
    bad_file = tmp_path / "corrupt.sqlite"
    bad_file.write_bytes(b"NOT A SQLITE FILE")
    threads = get_all_threads(bad_file)
    assert threads == []


@pytest.mark.anyio
async def test_main_handles_mcp_tools_failure(capsys):
    with (
        patch("builtins.input", side_effect=["exit"]),
        patch(
            "agent_cli.chat.get_tools_sync",
            side_effect=RuntimeError("MCP server connection refused"),
        ),
        patch("agent_cli.chat.build_graph"),
    ):
        await main()
    captured = capsys.readouterr()
    assert (
        "Warning: MCP tools unavailable: MCP server connection refused" in captured.out
    )


def test_handle_command_copy_no_response(capsys):
    config = {"configurable": {"thread_id": "test"}}
    handled = _handle_command("/copy", config, last_response=None)
    assert handled is True
    captured = capsys.readouterr()
    assert "No assistant response available to copy." in captured.out


def test_handle_command_copy_success(capsys):
    config = {"configurable": {"thread_id": "test"}}
    with patch("agent_cli.chat.copy_to_clipboard", return_value=True):
        handled = _handle_command("/copy", config, last_response="Hello AI")
        assert handled is True
        captured = capsys.readouterr()
        assert "Copied last response to clipboard!" in captured.out


def test_handle_command_copy_failure(capsys):
    config = {"configurable": {"thread_id": "test"}}
    with patch("agent_cli.chat.copy_to_clipboard", return_value=False):
        handled = _handle_command("/copy", config, last_response="Hello AI")
        assert handled is True
        captured = capsys.readouterr()
        assert "Warning: Could not copy to clipboard" in captured.out


def test_handle_command_export_success(capsys, tmp_path):
    config = {"configurable": {"thread_id": "thread-exp"}}
    mock_file = tmp_path / "conversation_thread-exp.md"
    with patch("agent_cli.chat.export_thread_to_markdown", return_value=mock_file):
        handled = _handle_command("/export my_exports", config)
        assert handled is True
        captured = capsys.readouterr()
        assert "Exported conversation to:" in captured.out
        assert str(mock_file) in captured.out


def test_handle_command_export_failure(capsys):
    config = {"configurable": {"thread_id": "thread-exp"}}
    with patch("agent_cli.chat.export_thread_to_markdown", return_value=None):
        handled = _handle_command("/export", config)
        assert handled is True
        captured = capsys.readouterr()
        assert "Could not export thread 'thread-exp'" in captured.out
