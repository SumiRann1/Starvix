from prompt_toolkit.formatted_text import HTML
from langgraph.store.base import BaseStore

from agent_cli.config import settings

THEMES: dict[str, dict[str, str]] = {
    "tokyo_night": {
        "bg": "#1a1b26",
        "fg": "#c0caf5",
        "model_color": "#9ece6a",
        "thread_color": "#7aa2f7",
        "memory_color": "#e0af68",
        "help_color": "#bb9af7",
    },
    "catppuccin": {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "model_color": "#a6e3a1",
        "thread_color": "#89b4fa",
        "memory_color": "#f9e2af",
        "help_color": "#fab387",
    },
    "dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "model_color": "#50fa7b",
        "thread_color": "#8be9fd",
        "memory_color": "#f1fa8c",
        "help_color": "#ff79c6",
    },
    "nord": {
        "bg": "#2e3440",
        "fg": "#eceff4",
        "model_color": "#a3be8c",
        "thread_color": "#88c0d0",
        "memory_color": "#ebcb8b",
        "help_color": "#b48ead",
    },
    "monokai": {
        "bg": "#272822",
        "fg": "#f8f8f2",
        "model_color": "#a6e22e",
        "thread_color": "#66d9ef",
        "memory_color": "#e6db74",
        "help_color": "#fd971f",
    },
    "cyberpunk": {
        "bg": "#0d0221",
        "fg": "#00f0ff",
        "model_color": "#05ffa1",
        "thread_color": "#00f0ff",
        "memory_color": "#ffe600",
        "help_color": "#ff2a6d",
    },
    "matrix": {
        "bg": "#0d1117",
        "fg": "#00ff66",
        "model_color": "#39ff14",
        "thread_color": "#20c20e",
        "memory_color": "#50c878",
        "help_color": "#00ffcc",
    },
    "minimal": {
        "bg": "#1c1c1c",
        "fg": "#e0e0e0",
        "model_color": "#4ade80",
        "thread_color": "#38bdf8",
        "memory_color": "#facc15",
        "help_color": "#f472b6",
    },
}


def resolve_statusbar_colors(sb_config=None) -> dict[str, str]:
    """Resolve statusbar theme and explicit color overrides from configuration."""
    sb = sb_config if sb_config is not None else getattr(settings, "statusbar", None)
    theme_name = getattr(sb, "theme", "tokyo_night") if sb else "tokyo_night"
    colors = dict(THEMES.get(theme_name, THEMES["tokyo_night"]))

    if sb:
        for key in ("bg", "fg", "model_color", "thread_color", "memory_color", "help_color"):
            val = getattr(sb, key, None)
            if val:
                colors[key] = val
    return colors


def get_statusline(config: dict, store: BaseStore | None = None) -> HTML:
    """Generate a formatted bottom status bar showing active model, thread, and memory stats."""
    configurable = config.get("configurable", {}) if config else {}
    current_model = configurable.get("model") or settings.current_model

    # Shorten model identifier for display
    if "/" in current_model:
        model_display = current_model.split("/")[-1]
    elif ":" in current_model:
        model_display = current_model.split(":")[-1]
    else:
        model_display = current_model

    if len(model_display) > 20:
        model_display = model_display[:18] + ".."

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
        except Exception:
            mem_count = 0

    c = resolve_statusbar_colors()

    return HTML(
        f'<style bg="{c["bg"]}" fg="{c["fg"]}"> '
        f'<b>[🤖 Model:</b> <style fg="{c["model_color"]}">{model_display}</style><b>]</b> '
        f'<b>[🧵 Thread:</b> <style fg="{c["thread_color"]}">{thread_display}</style><b>]</b> '
        f'<b>[🧠 Memories:</b> <style fg="{c["memory_color"]}">{mem_count}</style><b>]</b> '
        f'<b>[<style fg="{c["help_color"]}">⌨️  /help</style>]</b> '
        f'</style>'
    )
