import re
from pathlib import Path

IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "data",
    "workspaces",
    ".idea",
    ".vscode",
}

BINARY_EXTENSIONS = {
    ".sqlite",
    ".sqlite3",
    ".db",
    ".zip",
    ".tar",
    ".gz",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pyc",
    ".whl",
}

MAX_FILE_BYTES = 250_000  # 250 KB limit per attached file


def get_workspace_files(
    base_dir: Path | None = None, max_files: int = 250
) -> list[str]:
    """Retrieve relative paths of non-binary source files in the workspace."""
    root = Path(base_dir) if base_dir is not None else Path.cwd()
    if not root.exists():
        return []

    collected: list[str] = []
    try:
        for path in root.rglob("*"):
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() not in BINARY_EXTENSIONS:
                try:
                    rel = path.relative_to(root).as_posix()
                    collected.append(rel)
                    if len(collected) >= max_files:
                        break
                except ValueError:
                    continue
    except OSError:
        return []

    return sorted(collected)


def expand_file_mentions(
    query: str, base_dir: Path | None = None
) -> tuple[str, list[str]]:
    """Detect @filepath mentions in query and append file contents as Markdown context."""
    root = Path(base_dir) if base_dir is not None else Path.cwd()
    attached_files: list[str] = []
    file_attachments: list[str] = []

    # Match @filename or @path/to/file
    matches = list(re.finditer(r"@([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9_]+)", query))

    for m in matches:
        rel_str = m.group(1).replace("\\", "/")
        target_path = root / rel_str

        if (
            target_path.is_file()
            and target_path.suffix.lower() not in BINARY_EXTENSIONS
        ):
            if target_path.stat().st_size > MAX_FILE_BYTES:
                continue

            try:
                content = target_path.read_text(encoding="utf-8", errors="replace")
                ext = target_path.suffix.lstrip(".") or "text"
                attachment = (
                    f"\n\n--- [Attached File: {rel_str}] ---\n```{ext}\n{content}\n```"
                )
                file_attachments.append(attachment)
                attached_files.append(rel_str)
            except OSError:
                continue

    expanded_query = query + "".join(file_attachments)
    return expanded_query, attached_files
