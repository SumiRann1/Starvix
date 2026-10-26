from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_cli.config import settings


@dataclass
class ThemePalette:
    name: str
    bg: str
    fg: str
    primary: str
    secondary: str
    accent: str
    tool_badge: str
    success: str
    warning: str
    danger: str
    dim: str
    panel_border: str
    code_theme: str

    model_color: str
    thread_color: str
    memory_color: str
    help_color: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "bg": self.bg,
            "fg": self.fg,
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "tool_badge": self.tool_badge,
            "success": self.success,
            "warning": self.warning,
            "danger": self.danger,
            "dim": self.dim,
            "panel_border": self.panel_border,
            "code_theme": self.code_theme,
            "model_color": self.model_color,
            "thread_color": self.thread_color,
            "memory_color": self.memory_color,
            "help_color": self.help_color,
        }



THEME_REGISTRY: dict[str, ThemePalette] = {
    "strands": ThemePalette(
        name="strands",
        bg="#101213",
        fg="#eceff1",
        primary="#68f58a",
        secondary="#a2a9ad",
        accent="#68f58a",
        tool_badge="#68f58a",
        success="#68f58a",
        warning="#ffd166",
        danger="#ef476f",
        dim="#646c71",
        panel_border="#2b3135",
        code_theme="monokai",
        model_color="#eceff1",
        thread_color="#a2a9ad",
        memory_color="#68f58a",
        help_color="#68f58a",
    ),
    "tokyo_night": ThemePalette(
        name="tokyo_night",
        bg="#1a1b26",
        fg="#c0caf5",
        primary="#7aa2f7",
        secondary="#bb9af7",
        accent="#2ac3de",
        tool_badge="#e0af68",
        success="#9ece6a",
        warning="#e0af68",
        danger="#f7768e",
        dim="#565f89",
        panel_border="#3b4261",
        code_theme="tokyo-night",
        model_color="#9ece6a",
        thread_color="#7aa2f7",
        memory_color="#e0af68",
        help_color="#bb9af7",
    ),
    "catppuccin": ThemePalette(
        name="catppuccin",
        bg="#1e1e2e",
        fg="#cdd6f4",
        primary="#cba6f7",
        secondary="#89b4fa",
        accent="#f5c2e7",
        tool_badge="#fab387",
        success="#a6e3a1",
        warning="#f9e2af",
        danger="#f38ba8",
        dim="#6c7086",
        panel_border="#45475a",
        code_theme="catppuccin-mocha",
        model_color="#a6e3a1",
        thread_color="#89b4fa",
        memory_color="#f9e2af",
        help_color="#fab387",
    ),
    "dracula": ThemePalette(
        name="dracula",
        bg="#282a36",
        fg="#f8f8f2",
        primary="#bd93f9",
        secondary="#8be9fd",
        accent="#ff79c6",
        tool_badge="#ffb86c",
        success="#50fa7b",
        warning="#f1fa8c",
        danger="#ff5555",
        dim="#6272a4",
        panel_border="#44475a",
        code_theme="dracula",
        model_color="#50fa7b",
        thread_color="#8be9fd",
        memory_color="#f1fa8c",
        help_color="#ff79c6",
    ),
    "nord": ThemePalette(
        name="nord",
        bg="#2e3440",
        fg="#eceff4",
        primary="#88c0d0",
        secondary="#81a1c1",
        accent="#b48ead",
        tool_badge="#ebcb8b",
        success="#a3be8c",
        warning="#ebcb8b",
        danger="#bf616a",
        dim="#616e88",
        panel_border="#434c5e",
        code_theme="nord",
        model_color="#a3be8c",
        thread_color="#88c0d0",
        memory_color="#ebcb8b",
        help_color="#b48ead",
    ),
    "monokai": ThemePalette(
        name="monokai",
        bg="#272822",
        fg="#f8f8f2",
        primary="#a6e22e",
        secondary="#66d9ef",
        accent="#fd971f",
        tool_badge="#e6db74",
        success="#a6e22e",
        warning="#e6db74",
        danger="#f92672",
        dim="#75715e",
        panel_border="#49483e",
        code_theme="monokai",
        model_color="#a6e22e",
        thread_color="#66d9ef",
        memory_color="#e6db74",
        help_color="#fd971f",
    ),
    "cyberpunk": ThemePalette(
        name="cyberpunk",
        bg="#0d0221",
        fg="#00f0ff",
        primary="#00f0ff",
        secondary="#ff007f",
        accent="#ffe600",
        tool_badge="#05ffa1",
        success="#05ffa1",
        warning="#ffe600",
        danger="#ff2a6d",
        dim="#5e4b8b",
        panel_border="#711c91",
        code_theme="monokai",
        model_color="#05ffa1",
        thread_color="#00f0ff",
        memory_color="#ffe600",
        help_color="#ff2a6d",
    ),
    "spectre": ThemePalette(
        name="spectre",
        bg="#14171a",
        fg="#dee2e8",
        primary="#ff374c",
        secondary="#dee2e8",
        accent="#ff5e70",
        tool_badge="#ff374c",
        success="#4ade80",
        warning="#fbbf24",
        danger="#ff374c",
        dim="#848e9e",
        panel_border="#2d333b",
        code_theme="github-dark",
        model_color="#dee2e8",
        thread_color="#848e9e",
        memory_color="#ff374c",
        help_color="#ff374c",
    ),
    "matrix": ThemePalette(
        name="matrix",
        bg="#0d1117",
        fg="#00ff66",
        primary="#39ff14",
        secondary="#20c20e",
        accent="#00ffcc",
        tool_badge="#39ff14",
        success="#39ff14",
        warning="#e6db74",
        danger="#ff3333",
        dim="#1c542d",
        panel_border="#164424",
        code_theme="monokai",
        model_color="#39ff14",
        thread_color="#20c20e",
        memory_color="#50c878",
        help_color="#00ffcc",
    ),
    "minimal": ThemePalette(
        name="minimal",
        bg="#1c1c1c",
        fg="#e0e0e0",
        primary="#e0e0e0",
        secondary="#94a3b8",
        accent="#38bdf8",
        tool_badge="#38bdf8",
        success="#4ade80",
        warning="#facc15",
        danger="#f87171",
        dim="#64748b",
        panel_border="#334155",
        code_theme="native",
        model_color="#4ade80",
        thread_color="#38bdf8",
        memory_color="#facc15",
        help_color="#f472b6",
    ),
}

THEMES: dict[str, dict[str, str]] = {k: v.to_dict() for k, v in THEME_REGISTRY.items()}


def get_current_theme(sb_config: Any = None) -> ThemePalette:
    """Retrieve active ThemePalette with user configuration overrides applied."""
    sb = sb_config if sb_config is not None else getattr(settings, "statusbar", None)
    theme_name = getattr(sb, "theme", "tokyo_night") if sb else "tokyo_night"
    base = THEME_REGISTRY.get(theme_name, THEME_REGISTRY["tokyo_night"])

    # Build copy to allow explicit YAML overrides
    data = base.to_dict()
    if sb:
        for key in (
            "bg",
            "fg",
            "model_color",
            "thread_color",
            "memory_color",
            "help_color",
        ):
            val = getattr(sb, key, None)
            if val:
                data[key] = val
                if key == "model_color":
                    data["primary"] = val
                elif key == "help_color":
                    data["accent"] = val

    return ThemePalette(**data)
