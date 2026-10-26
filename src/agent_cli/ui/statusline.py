from pathlib import Path

from langgraph.store.base import BaseStore
from prompt_toolkit.formatted_text import HTML

from agent_cli.config import settings

from agent_cli.ui.theme import THEMES, get_current_theme


def resolve_statusbar_colors(sb_config=None) -> dict[str, str]:
    """Resolve statusbar theme and explicit color overrides from configuration."""
    theme = get_current_theme(sb_config)
    return theme.to_dict()



def get_statusline(config: dict, store: BaseStore | None = None) -> HTML:
    """Generate a formatted bottom status bar inspired by Strands CLI."""
    configurable = config.get("configurable", {}) if config else {}
    current_model = configurable.get("model") or settings.current_model

    # Shorten model identifier for display
    if "/" in current_model:
        model_display = current_model.split("/")[-1]
    elif ":" in current_model:
        model_display = current_model.split(":")[-1]
    else:
        model_display = current_model

    if len(model_display) > 28:
        model_display = model_display[:26] + ".."

    thread_id = configurable.get("thread_id", "-")
    if len(thread_id) > 16:
        thread_display = thread_id[:14] + ".."
    else:
        thread_display = thread_id

    mem_count = 0
    if store is not None:
        try:
            items = store.search(("memories", "default"), limit=1000)
            mem_count = len(items)
        except Exception:  # noqa: BLE001
            mem_count = 0

    try:
        cwd = Path.cwd()
        home = Path.home()
        if cwd == home:
            path_display = "~"
        elif cwd.is_relative_to(home):
            path_display = f"~/{cwd.relative_to(home)}"
        else:
            path_display = str(cwd)
        if len(path_display) > 35:
            path_display = "..." + path_display[-32:]
    except Exception:  # noqa: BLE001
        path_display = "workspace"

    c = resolve_statusbar_colors()
    div = f'<style fg="{c["dim"]}">│</style>'

    return HTML(
        f'<style bg="{c["bg"]}" fg="{c["fg"]}">'
        f' <style fg="{c["primary"]}"><b>✦ Starvix</b></style> '
        f'{div} <style fg="{c["model_color"]}"><b>{model_display}</b></style> '
        f'{div} <style fg="{c["thread_color"]}">Thread: {thread_display}</style> '
        f'{div} <b>Memories:</b> <style fg="{c["memory_color"]}">{mem_count}</style> '
        f'{div} <style fg="{c["dim"]}">{path_display}</style> '
        f'{div} <style fg="{c["help_color"]}">/help</style> '
        f"</style>"
    )
