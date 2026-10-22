import sys
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown


class MarkdownStreamRenderer:
    """Renders streaming LLM text in real-time as formatted Markdown with syntax highlighting."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.live: Live | None = None
        self.accumulated_text = ""
        self.started = False
        self._is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def start(self) -> None:
        """Begin streaming output."""
        self.accumulated_text = ""
        if self._is_tty:
            self.live = Live(
                Markdown(""),
                console=self.console,
                refresh_per_second=12,
                transient=False,
            )
            self.live.start()
        else:
            self.console.print("[bold]Assistant:[/bold] ", end="")
        self.started = True

    def write_chunk(self, chunk: str) -> None:
        """Stream an incoming chunk to the terminal."""
        if not chunk:
            return
        if not self.started:
            self.start()

        self.accumulated_text += chunk
        if self.live and self._is_tty:
            self.live.update(Markdown(self.accumulated_text))
        else:
            print(chunk, end="", flush=True)

    def finish(self) -> str:
        """Conclude streaming and ensure final Markdown is flushed."""
        if self.started:
            if self.live and self._is_tty:
                self.live.update(Markdown(self.accumulated_text))
                self.live.stop()
                self.live = None
            else:
                print()
            self.started = False
        return self.accumulated_text
