import subprocess
from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent_cli.ui.export import copy_to_clipboard, export_thread_to_markdown


def test_copy_to_clipboard_empty_text():
    assert copy_to_clipboard("") is False
    assert copy_to_clipboard(None) is False


def test_copy_to_clipboard_pyperclip_success():
    with patch("pyperclip.copy") as mock_copy:
        res = copy_to_clipboard("test clipboard text")
        assert res is True
        mock_copy.assert_called_once_with("test clipboard text")


def test_copy_to_clipboard_fallback_wl_copy_success():
    with (
        patch("pyperclip.copy", side_effect=Exception("No xclip/pyperclip")),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = Mock(returncode=0)
        res = copy_to_clipboard("wl copy text")
        assert res is True
        mock_run.assert_called_once_with(
            ["wl-copy"],
            input=b"wl copy text",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def test_copy_to_clipboard_fallback_xclip_success():
    def fake_subprocess_run(cmd, **kwargs):
        if cmd[0] == "wl-copy":
            raise OSError("wl-copy not found")
        if cmd[0] == "xclip":
            return Mock(returncode=0)
        return Mock(returncode=1)

    with (
        patch("pyperclip.copy", side_effect=Exception("No pyperclip")),
        patch("subprocess.run", side_effect=fake_subprocess_run),
    ):
        res = copy_to_clipboard("xclip text")
        assert res is True


def test_copy_to_clipboard_all_fail():
    with (
        patch("pyperclip.copy", side_effect=Exception("Failed")),
        patch("subprocess.run", side_effect=OSError("Not found")),
    ):
        res = copy_to_clipboard("fail text")
        assert res is False


def test_export_thread_to_markdown_nonexistent_db(tmp_path):
    res = export_thread_to_markdown("thread-1", tmp_path / "nonexistent.sqlite")
    assert res is None


@pytest.mark.anyio
async def test_export_thread_to_markdown_valid(tmp_path):
    db_path = tmp_path / "test_checkpoints.sqlite"
    thread_id = "test-export-thread"
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    # Create checkpoints using AsyncSqliteSaver
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as saver:
        await saver.setup()
        checkpoint = {
            "v": 1,
            "ts": "2026-10-22T10:00:00Z",
            "id": "cp1",
            "channel_values": {
                "messages": [
                    HumanMessage(content="Hello world"),
                    AIMessage(content="Hi there!"),
                    ToolMessage(content="Result from tool", tool_call_id="call_1", name="search_tool"),
                ]
            },
            "channel_versions": {},
            "versions_seen": {},
        }
        await saver.aput(config, checkpoint, {}, {})

    out_dir = tmp_path / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    with patch("agent_cli.ui.export.settings.export_dir", out_dir):
        exported_file = export_thread_to_markdown(thread_id, db_path)

        assert exported_file is not None
        assert exported_file.exists()
        assert exported_file.name == f"conversation_{thread_id}.md"

        content = exported_file.read_text(encoding="utf-8")
        assert f"# Conversation Export: `{thread_id}`" in content
        assert "### 👤 User\nHello world" in content
        assert "### 🤖 Assistant\nHi there!" in content
        assert "### 🛠️ Tool: `search_tool`" in content
        assert "Result from tool" in content


@pytest.mark.anyio
async def test_export_thread_to_markdown_empty_messages(tmp_path):
    db_path = tmp_path / "empty_checkpoints.sqlite"
    thread_id = "empty-thread"
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as saver:
        await saver.setup()
        checkpoint = {
            "v": 1,
            "ts": "2026-10-22T10:00:00Z",
            "id": "cp_empty",
            "channel_values": {"messages": []},
            "channel_versions": {},
            "versions_seen": {},
        }
        await saver.aput(config, checkpoint, {}, {})

    res = export_thread_to_markdown(thread_id, db_path)
    assert res is None


def test_export_thread_to_markdown_handles_exception(tmp_path):
    bad_db = tmp_path / "corrupt.sqlite"
    bad_db.write_text("corrupted content", encoding="utf-8")
    res = export_thread_to_markdown("any-thread", bad_db)
    assert res is None
