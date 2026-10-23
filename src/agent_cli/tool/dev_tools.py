import os
import subprocess
from pathlib import Path

from langchain_core.tools import tool
from langgraph.types import interrupt

from agent_cli.config import settings

WORKSPACE = Path(settings.workspace_dir)


def _resolve_safe_path(path_str: str) -> Path | None:
    """Resolve path and ensure it stays strictly within the workspace."""
    try:
        target = (WORKSPACE / path_str).resolve()
        if target.is_relative_to(WORKSPACE.resolve()):
            return target
    except (ValueError, RuntimeError):
        pass
    return None


@tool
def list_files(directory: str = "."):
    """List all files in a workspace directory."""
    abs_path = _resolve_safe_path(directory)
    if abs_path is None:
        return f"Access denied: Directory '{directory}' is outside the workspace."
    if not abs_path.exists():
        return f"Directory not found: {directory}"
    return [f.name for f in abs_path.iterdir()]


@tool
def grep_search(query: str, path: str = "."):
    """Search for a text pattern inside files in the workspace (case-insensitive)."""
    abs_path = _resolve_safe_path(path)
    if abs_path is None:
        return f"Access denied: Path '{path}' is outside the workspace."
    if not abs_path.exists():
        return f"Directory not found: {path}"

    matches = []
    files_to_check = [abs_path] if abs_path.is_file() else abs_path.rglob("*")

    for file in files_to_check:
        if file.is_file():
            # Skip hidden and cache folders
            if any(part in file.parts for part in (".git", "__pycache__", ".venv", "node_modules", ".pytest_cache")):
                continue
            try:
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            rel_path = file.relative_to(WORKSPACE)
                            matches.append(f"{rel_path}:{line_no}: {line.strip()}")
                            if len(matches) >= 50:
                                return "\n".join(matches) + "\n... (more matches truncated)"
            except Exception: # noqa: BLE001, S112
                continue

    return "\n".join(matches) if matches else f"No matches found for '{query}'"


@tool
def find_files(query: str, directory: str = "."):
    """Find files matching a name pattern in the workspace."""
    abs_path = _resolve_safe_path(directory)
    if abs_path is None:
        return f"Access denied: Directory '{directory}' is outside the workspace."
    if not abs_path.exists():
        return f"Directory not found: {directory}"

    matched = []
    for f in abs_path.rglob(f"*{query}*"):
        if f.is_file():
            matched.append(str(f.relative_to(WORKSPACE)))
            if len(matched) >= 50:
                break
    return matched if matched else f"No files matching '{query}' found."


@tool
def read_file(file_path: str):
    """Read full content of a file in the workspace."""
    abs_path = _resolve_safe_path(file_path)
    if abs_path is None:
        return f"Access denied: File '{file_path}' is outside the workspace."
    if not abs_path.exists():
        return f"File not found: {file_path}"
    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


@tool
def read_relevant_lines(file_path: str, start_line: int, end_line: int):
    """Read a specific range of lines from a file in the workspace (1-indexed)."""
    abs_path = _resolve_safe_path(file_path)
    if abs_path is None:
        return f"Access denied: File '{file_path}' is outside the workspace."
    if not abs_path.exists():
        return f"File not found: {file_path}"
    try:
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        selected = lines[start_idx:end_idx]
        return "".join(f"{idx}: {line}" for idx, line in enumerate(selected, start=start_idx + 1))
    except Exception as exc: # noqa: BLE001
        return f"Error reading file: {exc}"


@tool
def get_file_outlines(file_path: str):
    """Extract outline of a file (classes, functions, and key definitions)."""
    abs_path = _resolve_safe_path(file_path)
    if abs_path is None:
        return f"Access denied: File '{file_path}' is outside the workspace."
    if not abs_path.exists():
        return f"File not found: {file_path}"

    try:
        content = abs_path.read_text(encoding="utf-8", errors="ignore")
        if file_path.endswith(".py"):
            import ast
            tree = ast.parse(content)
            outlines = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    outlines.append(f"Class: {node.name} (line {node.lineno})")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    outlines.append(f"Function: {node.name} (line {node.lineno})")
            return "\n".join(outlines) if outlines else "No functions or classes found."
        else:
            outlines = []
            for idx, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith(("#", "def ", "class ", "function ", "export ", "const ", "interface ")):
                    outlines.append(f"Line {idx}: {stripped}")
            return "\n".join(outlines[:50]) if outlines else "No outline markers found."
    except Exception as exc: # noqa: BLE001
        return f"Could not parse file: {exc}"


@tool
def write_file(file_path: str, content: str):
    """Write or overwrite a file in the workspace."""
    abs_path = _resolve_safe_path(file_path)
    if abs_path is None:
        return f"Access denied: File '{file_path}' is outside the workspace."

    approval = interrupt({
        "action": "write_file",
        "file_path": file_path,
        "message": f"Write file '{file_path}'?",
    })
    if approval not in (True, "y", "yes"):
        return f"Operation cancelled by user: '{file_path}' was NOT written."

    abs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File written: {file_path}"


@tool
def replace_code(file_path: str, old_code: str, new_code: str):
    """Replace specific code snippet in a file in the workspace."""
    abs_path = _resolve_safe_path(file_path)
    if abs_path is None:
        return f"Access denied: File '{file_path}' is outside the workspace."
    if not abs_path.exists():
        return f"File not found: {file_path}"

    approval = interrupt({
        "action": "replace_code",
        "file_path": file_path,
        "old_code": old_code,
        "new_code": new_code,
        "message": f"Replace code in '{file_path}'?",
    })
    if approval not in (True, "y", "yes"):
        return f"Operation cancelled by user: '{file_path}' was NOT replaced."

    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    if old_code not in content:
        return f"Error: Target code snippet not found in '{file_path}'."

    new_content = content.replace(old_code, new_code, 1)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return f"Code replaced in file: {file_path}"


@tool
def delete_file(file_path: str):
    """Delete a file in the workspace."""
    abs_path = _resolve_safe_path(file_path)
    if abs_path is None:
        return f"Access denied: File '{file_path}' is outside the workspace."
    if not abs_path.exists():
        return f"File not found: {file_path}"

    approved = interrupt({
        "action": "delete_file",
        "file_path": file_path,
        "message": f"Delete '{file_path}' from workspace ({abs_path})?",
    })

    if not approved or approved not in (True, "y", "yes"):
        return f"Operation cancelled by user: '{file_path}' was NOT deleted."

    os.remove(abs_path)
    return f"File successfully deleted: {file_path}"


@tool
def run_terminal_cmd(cmd: str):
    """Run a terminal command in the workspace directory. Requires human approval."""
    approval = interrupt({
        "action": "run_terminal_cmd",
        "cmd": cmd,
        "message": f"Run command '{cmd}'?",
    })
    if approval not in (True, "y", "yes"):
        return f"Operation cancelled by user: '{cmd}' was NOT executed."

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE),
            timeout=120,
        )
        output = proc.stdout
        if proc.stderr:
            output += ("\n[stderr]\n" + proc.stderr)
        return output.strip() if output.strip() else f"Command completed with exit code {proc.returncode}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 120 seconds."
    except Exception as exc: # noqa: BLE001
        return f"Command execution failed: {exc}"


@tool
def git_status():
    """Check git status of the workspace repository."""
    try:
        res = subprocess.run(
            ["git", "status", "--short"],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE),
        )
        return res.stdout if res.stdout else "Working tree clean."
    except Exception as exc: # noqa: BLE001
        return f"Git status error: {exc}"


dev_tools = [
    list_files,
    find_files,
    grep_search,
    read_file,
    read_relevant_lines,
    get_file_outlines,
    write_file,
    replace_code,
    delete_file,
    run_terminal_cmd,
    git_status,
]