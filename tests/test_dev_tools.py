import subprocess
from unittest.mock import Mock, patch

import pytest

from agent_cli.tool.dev_tools import (
    delete_file,
    dev_tools,
    find_files,
    get_file_outlines,
    git_status,
    grep_search,
    list_files,
    read_file,
    read_relevant_lines,
    replace_code,
    run_terminal_cmd,
    write_file,
)


@pytest.fixture
def workspace(tmp_path):
    """Fixture to isolate tool operations to a temporary directory."""
    with patch("agent_cli.tool.dev_tools.WORKSPACE", tmp_path):
        yield tmp_path


# --- list_files tests ---
def test_list_files_success(workspace):
    (workspace / "a.txt").write_text("hello")
    (workspace / "b.py").write_text("print(1)")
    (workspace / "subdir").mkdir()

    res = list_files.invoke({"directory": "."})
    assert isinstance(res, list)
    assert "a.txt" in res
    assert "b.py" in res
    assert "subdir" in res


def test_list_files_directory_not_found(workspace):
    res = list_files.invoke({"directory": "non_existent_folder"})
    assert "Directory not found" in res


# --- grep_search tests ---
def test_grep_search_found(workspace):
    (workspace / "sample.py").write_text("def find_me():\n    return 42\n")
    (workspace / "other.py").write_text("# nothing here\n")

    res = grep_search.invoke({"query": "find_me", "path": "."})
    assert "sample.py:1: def find_me():" in res
    assert "other.py" not in res


def test_grep_search_not_found(workspace):
    (workspace / "sample.py").write_text("apple banana")
    res = grep_search.invoke({"query": "orange", "path": "."})
    assert "No matches found for 'orange'" in res


def test_grep_search_skips_git_and_cache(workspace):
    git_dir = workspace / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("secret_keyword")

    (workspace / "code.py").write_text("secret_keyword here")

    res = grep_search.invoke({"query": "secret_keyword", "path": "."})
    assert "code.py" in res
    assert ".git" not in res


def test_grep_search_directory_not_found(workspace):
    res = grep_search.invoke({"query": "foo", "path": "does_not_exist"})
    assert "Directory not found" in res


# --- find_files tests ---
def test_find_files_success(workspace):
    sub = workspace / "nested"
    sub.mkdir()
    (sub / "special_service.py").write_text("# service")
    (workspace / "other.txt").write_text("other")

    res = find_files.invoke({"query": "special", "directory": "."})
    assert isinstance(res, list)
    assert any("special_service.py" in f for f in res)


def test_find_files_none_found(workspace):
    res = find_files.invoke({"query": "missing", "directory": "."})
    assert "No files matching 'missing' found." in res


def test_find_files_directory_not_found(workspace):
    res = find_files.invoke({"query": "a", "directory": "not_there"})
    assert "Directory not found" in res


# --- read_file tests ---
def test_read_file_success(workspace):
    (workspace / "test.txt").write_text("Hello World!")
    res = read_file.invoke({"file_path": "test.txt"})
    assert res == "Hello World!"


def test_read_file_not_found(workspace):
    res = read_file.invoke({"file_path": "missing.txt"})
    assert "File not found" in res


# --- read_relevant_lines tests ---
def test_read_relevant_lines_success(workspace):
    content = "\n".join([f"Line {i}" for i in range(1, 11)])
    (workspace / "multiline.txt").write_text(content)

    res = read_relevant_lines.invoke(
        {"file_path": "multiline.txt", "start_line": 3, "end_line": 5}
    )
    assert "3: Line 3" in res
    assert "4: Line 4" in res
    assert "5: Line 5" in res
    assert "1: Line 1" not in res
    assert "6: Line 6" not in res


def test_read_relevant_lines_not_found(workspace):
    res = read_relevant_lines.invoke(
        {"file_path": "missing.txt", "start_line": 1, "end_line": 2}
    )
    assert "File not found" in res


# --- get_file_outlines tests ---
def test_get_file_outlines_python(workspace):
    py_code = """
class Calculator:
    def add(self, a, b):
        return a + b

def helper():
    pass
"""
    (workspace / "calc.py").write_text(py_code)
    res = get_file_outlines.invoke({"file_path": "calc.py"})
    assert "Class: Calculator" in res
    assert "Function: add" in res
    assert "Function: helper" in res


def test_get_file_outlines_markdown(workspace):
    md_content = """# Main Header
Some text
## Subheader 1
def some_js():
    pass
"""
    (workspace / "doc.md").write_text(md_content)
    res = get_file_outlines.invoke({"file_path": "doc.md"})
    assert "# Main Header" in res
    assert "## Subheader 1" in res


def test_get_file_outlines_not_found(workspace):
    res = get_file_outlines.invoke({"file_path": "no_file.py"})
    assert "File not found" in res


# --- write_file tests ---
def test_write_file_creates_file_and_parents(workspace):
    nested_path = "src/modules/new_service.py"
    with patch("agent_cli.tool.dev_tools.interrupt", return_value=True):
        res = write_file.invoke(
            {"file_path": nested_path, "content": "print('created')"}
        )
        assert "File written: src/modules/new_service.py" in res

    created = workspace / "src" / "modules" / "new_service.py"
    assert created.exists()
    assert created.read_text() == "print('created')"


def test_write_file_cancelled(workspace):
    file_p = workspace / "cancelled.py"
    with patch("agent_cli.tool.dev_tools.interrupt", return_value=False):
        res = write_file.invoke(
            {"file_path": "cancelled.py", "content": "print('cancelled')"}
        )
        assert "Operation cancelled by user" in res
    assert not file_p.exists()


# --- replace_code (HITL) tests ---
def test_replace_code_approved(workspace):
    file_p = workspace / "code.py"
    file_p.write_text("old_function_name()")

    with patch("agent_cli.tool.dev_tools.interrupt", return_value=True):
        res = replace_code.invoke(
            {
                "file_path": "code.py",
                "old_code": "old_function_name",
                "new_code": "new_function_name",
            }
        )
        assert "Code replaced in file" in res
        assert file_p.read_text() == "new_function_name()"


def test_replace_code_cancelled(workspace):
    file_p = workspace / "code.py"
    file_p.write_text("old_code()")

    with patch("agent_cli.tool.dev_tools.interrupt", return_value=False):
        res = replace_code.invoke(
            {
                "file_path": "code.py",
                "old_code": "old_code",
                "new_code": "new_code",
            }
        )
        assert "Operation cancelled by user" in res
        assert file_p.read_text() == "old_code()"


def test_replace_code_snippet_not_found(workspace):
    file_p = workspace / "code.py"
    file_p.write_text("def hello(): pass")

    with patch("agent_cli.tool.dev_tools.interrupt", return_value=True):
        res = replace_code.invoke(
            {
                "file_path": "code.py",
                "old_code": "def goodbye():",
                "new_code": "def updated():",
            }
        )
        assert "Target code snippet not found" in res


def test_replace_code_file_not_found(workspace):
    res = replace_code.invoke(
        {
            "file_path": "non_existent.py",
            "old_code": "a",
            "new_code": "b",
        }
    )
    assert "File not found" in res


# --- delete_file (HITL) tests ---
def test_delete_file_approved(workspace):
    target = workspace / "to_delete.txt"
    target.write_text("goodbye")

    with patch("agent_cli.tool.dev_tools.interrupt", return_value=True):
        res = delete_file.invoke({"file_path": "to_delete.txt"})
        assert "File successfully deleted: to_delete.txt" in res
        assert not target.exists()


def test_delete_file_cancelled(workspace):
    target = workspace / "preserve_me.txt"
    target.write_text("keep this")

    with patch("agent_cli.tool.dev_tools.interrupt", return_value=False):
        res = delete_file.invoke({"file_path": "preserve_me.txt"})
        assert "Operation cancelled by user" in res
        assert target.exists()


def test_delete_file_not_found(workspace):
    res = delete_file.invoke({"file_path": "ghost.txt"})
    assert "File not found" in res


# --- run_terminal_cmd (HITL) tests ---
def test_run_terminal_cmd_approved(workspace):
    with (
        patch("agent_cli.tool.dev_tools.interrupt", return_value=True),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = Mock(stdout="pytest passed\n", stderr="", returncode=0)
        res = run_terminal_cmd.invoke({"cmd": "pytest"})
        assert "pytest passed" in res
        mock_run.assert_called_once()


def test_run_terminal_cmd_cancelled(workspace):
    with (
        patch("agent_cli.tool.dev_tools.interrupt", return_value=False),
        patch("subprocess.run") as mock_run,
    ):
        res = run_terminal_cmd.invoke({"cmd": "echo 'cancelling'"})
        assert "Operation cancelled by user" in res
        mock_run.assert_not_called()


def test_run_terminal_cmd_blocked_by_guardrails(workspace):
    with patch("agent_cli.tool.dev_tools.interrupt") as mock_interrupt:
        res = run_terminal_cmd.invoke({"cmd": "rm -rf ."})
        assert "Execution Blocked by Guardrails" in res
        assert "Dangerous command detected" in res
        mock_interrupt.assert_not_called()


def test_run_terminal_cmd_timeout(workspace):
    with (
        patch("agent_cli.tool.dev_tools.interrupt", return_value=True),
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="sleep 1000", timeout=120),
        ),
    ):
        res = run_terminal_cmd.invoke({"cmd": "sleep 1000"})
        assert "Command timed out" in res


# --- git_status tests ---
def test_git_status_clean(workspace):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(stdout="", returncode=0)
        res = git_status.invoke({})
        assert res == "Working tree clean."


def test_git_status_dirty(workspace):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            stdout=" M sample.py\n?? untracked.txt\n", returncode=0
        )
        res = git_status.invoke({})
        assert "M sample.py" in res


# --- dev_tools collection test ---
def test_dev_tools_list_registration():
    expected_names = {
        "list_files",
        "find_files",
        "grep_search",
        "read_file",
        "read_relevant_lines",
        "get_file_outlines",
        "write_file",
        "replace_code",
        "delete_file",
        "run_terminal_cmd",
        "git_status",
    }
    registered_names = {t.name for t in dev_tools}
    assert expected_names.issubset(registered_names)
    assert len(dev_tools) == len(expected_names)


# --- Workspace boundary security tests ---
def test_read_file_rejects_path_outside_workspace(tmp_path):
    # Create a workspace directory and an outside file
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "outside_secret.txt"
    outside_file.write_text("classified data")

    with patch("agent_cli.tool.dev_tools.WORKSPACE", workspace):
        # 1. Attempt relative traversal reading
        res_rel = read_file.invoke({"file_path": "../outside_secret.txt"})
        assert "Access denied" in res_rel
        assert "classified data" not in res_rel

        # 2. Attempt absolute path reading outside workspace
        res_abs = read_file.invoke({"file_path": str(outside_file)})
        assert "Access denied" in res_abs
        assert "classified data" not in res_abs


def test_write_file_rejects_path_outside_workspace(tmp_path):
    # Attempt to write outside the workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "malicious_file.txt"

    with patch("agent_cli.tool.dev_tools.WORKSPACE", workspace):
        # 1. Attempt to write outside via relative traversal
        res_rel = write_file.invoke(
            {"file_path": "../malicious_file.txt", "content": "injected"}
        )
        assert "Access denied" in res_rel
        assert not outside_file.exists()

        # 2. Attempt to write outside via absolute path
        res_abs = write_file.invoke(
            {"file_path": str(outside_file), "content": "injected"}
        )
        assert "Access denied" in res_abs
        assert not outside_file.exists()


def test_delete_file_rejects_path_outside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "important_outside.txt"
    outside_file.write_text("do not delete")

    with patch("agent_cli.tool.dev_tools.WORKSPACE", workspace):
        res = delete_file.invoke({"file_path": "../important_outside.txt"})
        assert "Access denied" in res
        assert outside_file.exists()


def test_other_tools_reject_path_outside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with patch("agent_cli.tool.dev_tools.WORKSPACE", workspace):
        assert "Access denied" in list_files.invoke({"directory": "../outside"})
        assert "Access denied" in grep_search.invoke(
            {"query": "q", "path": "../outside"}
        )
        assert "Access denied" in find_files.invoke(
            {"query": "q", "directory": "../outside"}
        )
        assert "Access denied" in replace_code.invoke(
            {"file_path": "../outside", "old_code": "a", "new_code": "b"}
        )
