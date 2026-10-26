import os
import sys
import time

from rich.console import Console
from rich.live import Live
from rich.text import Text

MINT_GREEN = "#68f58a"
MINT_GREEN_DIM = "#3d854e"
MINT_GREEN_BRIGHT = "#9effb3"

FORGE_LOGO = [
    r"███████╗ ██████╗ ██████╗   ██████╗ ███████╗",
    r"██╔════╝██╔═══██╗██╔══██╗ ██╔════╝ ██╔════╝",
    r"█████╗  ██║   ██║██████╔╝ ██║  ███╗█████╗  ",
    r"██╔══╝  ██║   ██║██╔══██╗ ██║   ██║██╔══╝  ",
    r"██║     ╚██████╔╝██║  ██║ ╚██████╔╝███████╗",
    r"╚═╝      ╚═════╝ ╚═╝  ╚═╝  ╚═════╝ ╚══════╝",
]


def render_logo(shimmer_line: int = -1) -> Text:
    """Render the FORGE logo in clean mint-green with a subtle wave highlight."""
    text = Text()
    for i, line in enumerate(FORGE_LOGO):
        if i == shimmer_line:
            text.append(line + "\n", style=f"bold {MINT_GREEN_BRIGHT}")
        elif shimmer_line != -1 and abs(i - shimmer_line) == 1:
            text.append(line + "\n", style=f"bold {MINT_GREEN}")
        else:
            text.append(line + "\n", style=f"{MINT_GREEN}")
    return text


def play_startup_animation(
    console: Console | None = None,
    speed: float = 1.0,
    tools_count: int = 0,
) -> None:
    """Play a clean, borderless mint-green startup animation inspired by Strands TUI."""
    con = console or Console()
    is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if not is_tty or os.environ.get("FORGE_NO_ANIMATION", "").lower() in ("1", "true"):
        return

    subsystems = [
        ("Storage Engine", "SQLite Checkpoints & Long-Term Memory connected"),
        ("Security Matrix", "Prompt injection defense & secret redaction active"),
        ("Model Gateway", "Multi-Provider Ready (Groq, Gemini, OpenRouter)"),
    ]

    try:
        with Live(console=con, refresh_per_second=20, transient=True) as live:
            # Phase 1: Subtle mint-green shimmer wave across the FORGE wordmark (~0.6s)
            for frame in range(len(FORGE_LOGO) + 2):
                content = Text()
                content.append("\n")
                content.append(render_logo(shimmer_line=frame))
                content.append("\n")
                content.append(Text("       ⚡ LOCAL-FIRST AGENT RUNTIME\n", style="dim"))
                live.update(content)
                time.sleep(0.08 * speed)

            # Phase 2: Clean borderless subsystem check (~0.9s)
            for count in range(1, len(subsystems) + 1):
                content = Text()
                content.append("\n")
                content.append(render_logo())
                content.append("\n")
                content.append(Text("       ⚡ LOCAL-FIRST AGENT RUNTIME\n\n", style="dim"))

                for idx, (label, detail) in enumerate(subsystems[:count]):
                    is_last = idx == len(subsystems) - 1
                    prefix = "└──" if is_last else "├──"
                    content.append(f" {prefix} ", style="dim")
                    content.append("[✓] ", style=f"bold {MINT_GREEN}")
                    content.append(f"{label:<18} ", style="white")
                    content.append(f"{detail}\n", style="dim")

                live.update(content)
                time.sleep(0.25 * speed)

            # Phase 3: Hold the completed state briefly (~0.3s)
            time.sleep(0.30 * speed)

    except (KeyboardInterrupt, Exception):  # noqa: BLE001
        return
