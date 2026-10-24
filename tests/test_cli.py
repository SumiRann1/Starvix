from unittest.mock import patch

from typer.testing import CliRunner

from agent_cli.cli import app

runner = CliRunner()


def test_cli_status():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Forge Agent Runtime" in result.stdout
    assert "CLI initialized successfully." in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Forge — a local-first LangGraph agent runtime." in result.stdout
    assert "status" in result.stdout
    assert "threads" in result.stdout
    assert "chat" in result.stdout


def test_cli_no_args_shows_help():
    result = runner.invoke(app, [])
    # Typer with no_args_is_help=True exits with 0 or 2 depending on typer version
    assert "Forge — a local-first LangGraph agent runtime." in result.stdout


def test_cli_threads_empty():
    with patch("agent_cli.cli.get_all_threads", return_value=[]):
        result = runner.invoke(app, ["threads"])
        assert result.exit_code == 0
        assert "No saved threads found." in result.stdout


def test_cli_threads_with_results():
    with patch(
        "agent_cli.cli.get_all_threads", return_value=["session-alpha", "session-beta"]
    ):
        result = runner.invoke(app, ["threads"])
        assert result.exit_code == 0
        assert "Saved conversation threads:" in result.stdout
        assert "session-alpha" in result.stdout
        assert "session-beta" in result.stdout
        assert "forge chat --thread <id>" in result.stdout


def test_cli_chat_command():
    with (
        patch("agent_cli.cli.chat_main") as mock_chat_main,
        patch("asyncio.run") as mock_run,
    ):
        result = runner.invoke(app, ["chat"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        mock_chat_main.assert_called_once_with(thread_id=None)


def test_cli_chat_command_with_thread_option():
    with (
        patch("agent_cli.cli.chat_main") as mock_chat_main,
        patch("asyncio.run") as mock_run,
    ):
        result = runner.invoke(app, ["chat", "--thread", "my-custom-thread"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        mock_chat_main.assert_called_once_with(thread_id="my-custom-thread")


def test_cli_chat_interrupted():
    with (
        patch("agent_cli.cli.chat_main"),
        patch("asyncio.run", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(app, ["chat"])
        assert result.exit_code == 0
        assert "Chat interrupted." in result.stdout
