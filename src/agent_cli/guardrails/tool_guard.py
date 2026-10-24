from guardrails import Guard

from .validators import DangerousCommandBlocklistValidator, FilePathBlocklistValidator

# 1. Guard instance for file paths
file_guard = Guard().use(FilePathBlocklistValidator(on_fail="exception"))

# 2. Guard instance for shell commands
command_guard = Guard().use(DangerousCommandBlocklistValidator(on_fail="exception"))


def validate_file_path(path: str) -> None:
    """Validates that a target file path does not access protected/secret files.

    Raises:
        ValidationError: If path targets .env, .git, or other protected patterns.
    """
    file_guard.validate(path)


def validate_terminal_command(cmd: str) -> None:
    """Validates that a terminal command does not execute dangerous/destructive operations.

    Raises:
        ValidationError: If command matches dangerous patterns (e.g. rm -rf).
    """
    command_guard.validate(cmd)
