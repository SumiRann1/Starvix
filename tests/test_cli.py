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
    assert "chat" in result.stdout


def test_cli_no_args_shows_help():
    result = runner.invoke(app, [])
    # Typer with no_args_is_help=True exits with 0 or 2 depending on typer version
    assert "Forge — a local-first LangGraph agent runtime." in result.stdout


def test_cli_chat_command():
    with (
        patch("agent_cli.cli.chat_main"),
        patch("asyncio.run") as mock_run,
    ):
        result = runner.invoke(app, ["chat"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
