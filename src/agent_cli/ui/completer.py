from pathlib import Path
from typing import Any, ClassVar

from langgraph.store.base import BaseStore
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style


from agent_cli.config import settings

from .context import get_workspace_files
from .statusline import get_statusline


class ChatBotCompleter(Completer):
    """Interactive completer for slash commands, dynamic arguments, and @file mentions."""

    COMMANDS: ClassVar[dict[str, str]] = {
        "/help": "Show available commands",
        "/models": "Show available models",
        "/switch": "Switch to a different model",
        "/theme": "View or switch statusbar theme",
        "/thread": "Show current thread ID",
        "/threads": "List all saved threads",
        "/all-threads": "List all saved threads",
        "/new": "Start a new conversation thread",
        "/switch-thread": "Switch to an existing thread",
        "/list-memories": "List all memories",
        "/clear-memories": "Clear all memories",
        "/delete-memory": "Delete a memory by ID",
        "/copy": "Copy last assistant response to clipboard",
        "/export": "Export current thread to Markdown file",
        "/exit": "Exit the chat",
        "/quit": "Exit the chat",
    }

    def __init__(
        self, db_path: Path | str | None = None, store: BaseStore | None = None
    ):
        self.db_path = db_path
        self.store = store

    def get_completions(self, document: Any, complete_event: Any):
        text = document.text_before_cursor
        stripped = text.lstrip()

        # 1. Complete @file mentions anywhere in the query
        last_word = (
            text.rsplit(maxsplit=1)[-1] if text and not text.endswith(" ") else ""
        )
        if last_word.startswith("@"):
            query_prefix = last_word[1:].lower()
            files = get_workspace_files()
            for file_path in files:
                if file_path.lower().startswith(query_prefix):
                    yield Completion(
                        f"@{file_path}",
                        start_position=-len(last_word),
                        display_meta="Attach file context",
                    )
            return

        # 2. Dynamic argument completion (after a space)
        if " " in stripped:
            parts = stripped.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/switch":
                for model_key, model_val in settings.models.items():
                    if model_key.lower().startswith(arg.lower()):
                        yield Completion(
                            model_key, start_position=-len(arg), display_meta=model_val
                        )

            elif cmd == "/theme":
                from agent_cli.ui.statusline import THEMES

                for theme_name in THEMES.keys():
                    if theme_name.lower().startswith(arg.lower()):
                        yield Completion(
                            theme_name,
                            start_position=-len(arg),
                            display_meta="Statusbar Theme",
                        )

            elif cmd == "/switch-thread":
                from agent_cli.chat import get_all_threads

                for tid in get_all_threads(self.db_path):
                    if tid.lower().startswith(arg.lower()):
                        yield Completion(
                            tid, start_position=-len(arg), display_meta="Saved thread"
                        )

            elif cmd == "/delete-memory" and self.store is not None:
                try:
                    for item in self.store.search(("memories", "default"), limit=1000):
                        if item.key.lower().startswith(arg.lower()):
                            preview = item.value.get("fact", "")
                            meta = (
                                (preview[:30] + "...") if len(preview) > 30 else preview
                            )
                            yield Completion(
                                item.key, start_position=-len(arg), display_meta=meta
                            )
                except Exception:  # noqa: BLE001, S110
                    pass
            return


        # 3. Slash command completion
        if stripped.startswith("/"):
            for cmd, desc in self.COMMANDS.items():
                if cmd.startswith(stripped.lower()):
                    yield Completion(
                        cmd, start_position=-len(stripped), display_meta=desc
                    )


def create_chat_session(
    history_file: Path | str | None = None,
    db_path: Path | str | None = None,
    store: BaseStore | None = None,
    config: dict | None = None,
) -> PromptSession:
    """Create a configured PromptSession with persistent history, auto-suggest, autocomplete, and statusline."""
    completer = ChatBotCompleter(db_path=db_path, store=store)

    custom_style = Style.from_dict(
        {
            "": "#eceff1 bg:#202223",
            "prompt": "#68f58a bold bg:#202223",
            "placeholder": "#6c7086 italic bg:#202223",
            "bottom-toolbar": "#a2a9ad bg:#101213",
            "completion-menu.completion": "bg:#202223 #eceff1",
            "completion-menu.completion.current": "bg:#303233 #68f58a bold",
            "completion-menu.meta.completion": "bg:#181a1b #a2a9ad",
            "completion-menu.meta.completion.current": "bg:#303233 #eceff1",
        }
    )

    placeholder = HTML('<style fg="#6c7086" bg="#202223">Enter to send • Ctrl+J for newline • / for commands</style>')

    kwargs: dict[str, Any] = {
        "completer": completer,
        "complete_while_typing": True,
        "auto_suggest": AutoSuggestFromHistory(),
        "style": custom_style,
        "placeholder": placeholder,
    }

    if config is not None:
        kwargs["bottom_toolbar"] = lambda: get_statusline(config, store)

    if history_file is not None:
        kwargs["history"] = FileHistory(str(history_file))

    return PromptSession(**kwargs)

