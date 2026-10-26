from __future__ import annotations

import re
import sys
import time

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from agent_cli.ui.theme import get_current_theme


class MarkdownStreamRenderer:
    """Renders streaming LLM text in real-time as formatted Markdown with syntax highlighting and <think> support."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.live: Live | None = None
        self.accumulated_text = ""
        self.started = False
        self._is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

        # Chain-of-Thought handling
        self.in_think_block = False
        self.think_text = ""
        self.think_start_time: float | None = None
        self.think_panel_rendered = False

    def start(self) -> None:
        """Begin streaming output."""
        self.accumulated_text = ""
        self.think_text = ""
        self.in_think_block = False
        self.think_panel_rendered = False
        self.started = True

        if not self._is_tty:
            self.console.print("[bold]Assistant:[/bold] ", end="")

    def _ensure_live(self) -> None:
        """Ensure Live display is active for the main response."""
        if self._is_tty and self.live is None:
            self.live = Live(
                Markdown(""),
                console=self.console,
                refresh_per_second=14,
                transient=False,
            )
            self.live.start()

    def write_chunk(self, chunk: str) -> None:
        """Stream an incoming chunk to the terminal, routing <think> tokens cleanly."""
        if not chunk:
            return
        if not self.started:
            self.start()

        self.accumulated_text += chunk
        theme = get_current_theme()

        # Handle <think> tags if present in the stream
        if "<think>" in chunk and not self.in_think_block:
            self.in_think_block = True
            self.think_start_time = time.perf_counter()
            # If there was text before <think>, flush it
            parts = chunk.split("<think>", 1)
            before = parts[0]
            after = parts[1]
            if before and self._is_tty:
                self._ensure_live()
                self.live.update(Markdown(self.accumulated_text.split("<think>")[0]))
            self.think_text += after
            if self._is_tty:
                self.console.print(f"[dim {theme.dim}]┌─ 🧠 Thinking...[/dim {theme.dim}]")
            return

        if self.in_think_block:
            if "</think>" in chunk:
                parts = chunk.split("</think>", 1)
                self.think_text += parts[0]
                self.in_think_block = False
                elapsed = time.perf_counter() - (self.think_start_time or time.perf_counter())
                if self._is_tty:
                    preview = self.think_text.strip().replace("\n", " ")
                    if len(preview) > 90:
                        preview = preview[:87] + "..."
                    self.console.print(f"[dim {theme.dim}]│ {preview}[/dim {theme.dim}]")
                    self.console.print(f"[dim {theme.dim}]└─ 🧠 Thought for {elapsed:.1f}s[/dim {theme.dim}]\n")
                after = parts[1]
                if after:
                    clean_main = self._get_display_text()
                    if self._is_tty:
                        self._ensure_live()
                        self.live.update(Markdown(clean_main))
                    else:
                        print(after, end="", flush=True)
            else:
                self.think_text += chunk
            return

        # Normal markdown stream outside of thinking
        display_text = self._get_display_text()
        if self._is_tty:
            self._ensure_live()
            self.live.update(Markdown(display_text, code_theme=theme.code_theme))
        else:
            print(chunk, end="", flush=True)

    def _get_display_text(self) -> str:
        """Strip raw <think>...</think> from the rendered markdown display."""
        if "<think>" in self.accumulated_text:
            cleaned = re.sub(r"<think>.*?</think>", "", self.accumulated_text, flags=re.DOTALL)
            return cleaned.lstrip()
        return self.accumulated_text

    def finish(self) -> str:
        """Conclude streaming and ensure final Markdown is flushed."""
        if self.started:
            if self.in_think_block and self._is_tty:
                self.in_think_block = False
                theme = get_current_theme()
                self.console.print(f"[dim {theme.dim}]└─ 🧠 Thought complete[/dim {theme.dim}]\n")

            if self.live and self._is_tty:
                theme = get_current_theme()
                self.live.update(Markdown(self._get_display_text(), code_theme=theme.code_theme))
                self.live.stop()
                self.live = None
            else:
                print()
            self.started = False
        return self.accumulated_text
