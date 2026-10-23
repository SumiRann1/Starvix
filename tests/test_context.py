
from agent_cli.ui.context import expand_file_mentions, get_workspace_files


def test_get_workspace_files(tmp_path):
    (tmp_path / "hello.py").write_text("print('hello')")
    (tmp_path / "notes.md").write_text("# Notes")
    (tmp_path / "data.sqlite").write_bytes(b"dummy db")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("dummy")

    files = get_workspace_files(base_dir=tmp_path)
    assert "hello.py" in files
    assert "notes.md" in files
    assert "data.sqlite" not in files
    assert not any(".git" in f for f in files)


def test_expand_file_mentions_present(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text("def add(a, b): return a + b")

    query = "Check this function: @sample.py"
    expanded, attached = expand_file_mentions(query, base_dir=tmp_path)

    assert attached == ["sample.py"]
    assert "Attached File: sample.py" in expanded
    assert "def add(a, b): return a + b" in expanded


def test_expand_file_mentions_non_existent(tmp_path):
    query = "Look at @does_not_exist.py"
    expanded, attached = expand_file_mentions(query, base_dir=tmp_path)
    assert attached == []
    assert expanded == query
