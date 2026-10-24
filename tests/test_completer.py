from unittest.mock import Mock, patch

from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document

from agent_cli.ui.completer import ChatBotCompleter, create_chat_session


def test_completer_slash_commands():
    completer = ChatBotCompleter()

    # Test typing '/'
    doc_slash = Document("/")
    completions = list(completer.get_completions(doc_slash, None))
    assert len(completions) == len(ChatBotCompleter.COMMANDS)
    assert any(c.text == "/help" for c in completions)
    assert any(c.text == "/switch" for c in completions)

    # Test filtering '/sw'
    doc_sw = Document("/sw")
    completions_sw = list(completer.get_completions(doc_sw, None))
    assert [c.text for c in completions_sw] == ["/switch", "/switch-thread"]


def test_completer_switch_models():
    completer = ChatBotCompleter()

    with patch(
        "agent_cli.ui.completer.settings.models",
        {"gpt_oss_20b": "model1", "gemini_flash": "model2"},
    ):
        doc = Document("/switch ")
        completions = list(completer.get_completions(doc, None))
        assert [c.text for c in completions] == ["gpt_oss_20b", "gemini_flash"]

        # Prefix filtering
        doc_prefix = Document("/switch gem")
        completions_prefix = list(completer.get_completions(doc_prefix, None))
        assert [c.text for c in completions_prefix] == ["gemini_flash"]


def test_completer_switch_threads():
    completer = ChatBotCompleter(db_path="dummy.sqlite")

    with patch(
        "agent_cli.chat.get_all_threads", return_value=["thread-alpha", "thread-beta"]
    ):
        doc = Document("/switch-thread ")
        completions = list(completer.get_completions(doc, None))
        assert [c.text for c in completions] == ["thread-alpha", "thread-beta"]


def test_completer_delete_memory():
    mock_store = Mock()
    mock_item = Mock()
    mock_item.key = "mem-xyz123"
    mock_item.value = {"fact": "User likes Python"}
    mock_store.search.return_value = [mock_item]

    completer = ChatBotCompleter(store=mock_store)

    doc = Document("/delete-memory ")
    completions = list(completer.get_completions(doc, None))
    assert [c.text for c in completions] == ["mem-xyz123"]
    assert completions[0].display_meta_text == "User likes Python"


def test_create_chat_session(tmp_path):
    history_file = tmp_path / ".history"
    session = create_chat_session(history_file=history_file)
    assert isinstance(session, PromptSession)
    assert session.completer is not None
    assert isinstance(session.completer, ChatBotCompleter)
