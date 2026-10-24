import datetime
import subprocess
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from agent_cli.config import settings


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard using pyperclip with CLI fallback."""
    if not text:
        return False

    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception:  # noqa: BLE001, S110
        pass

    # Fallback to Linux wl-copy (Wayland)
    try:
        proc = subprocess.run(
            ["wl-copy"],
            input=text.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0:
            return True
    except OSError:
        pass

    # Fallback to xclip (X11)
    try:
        proc = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0:
            return True
    except OSError:
        pass

    return False


def export_thread_to_markdown(
    thread_id: str,
    db_path: Path | str,
) -> Path | None:
    """Export thread conversation history to a beautifully formatted Markdown file."""
    target_db = Path(db_path)
    if not target_db.exists():
        return None

    try:
        with SqliteSaver.from_conn_string(str(target_db)) as saver:
            tuple_res = saver.get_tuple({"configurable": {"thread_id": thread_id}})
            if not tuple_res:
                return None

            channel_values = tuple_res.checkpoint.get("channel_values", {})
            messages = channel_values.get("messages", [])
            if not messages:
                return None

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines = [
                f"# Conversation Export: `{thread_id}`",
                f"*Generated on: {timestamp}*",
                "",
                "---",
                "",
            ]

            for msg in messages:
                cls_name = msg.__class__.__name__
                content = getattr(msg, "content", "")
                if not content and hasattr(msg, "tool_calls") and msg.tool_calls:
                    content = f"*Tool Call*: `{msg.tool_calls}`"

                if cls_name == "HumanMessage":
                    lines.append(f"### 👤 User\n{content}\n")
                elif cls_name == "AIMessage":
                    lines.append(f"### 🤖 Assistant\n{content}\n")
                elif cls_name == "ToolMessage":
                    tool_name = getattr(msg, "name", "tool")
                    lines.append(
                        f"### 🛠️ Tool: `{tool_name}`\n```text\n{content}\n```\n"
                    )
                else:
                    lines.append(f"### 💬 {cls_name}\n{content}\n")

            safe_tid = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in thread_id
            )
            out_file = settings.export_dir / f"conversation_{safe_tid}.md"
            out_file.write_text("\n".join(lines), encoding="utf-8")
            return out_file
    except Exception:  # noqa: BLE001
        return None
