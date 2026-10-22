import asyncio
import sqlite3
import time
import uuid
from pathlib import Path

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.base import BaseStore
from langgraph.store.sqlite.base import SqliteStore

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

from .config import set_current_model, settings
from .graph import build_graph
from .memory import clear_memories, delete_memory, get_all_memories, memory_tools
from .tool import get_tools_sync

CHECKPOINT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "checkpoints.sqlite"
STORE_DB_PATH = Path(__file__).parent.parent.parent / "data" / "store.sqlite"

def get_all_threads(db_path: Path | str | None = None) -> list[str]:
    """Retrieve all unique thread IDs stored in the SQLite checkpoints database."""
    target_path = Path(db_path) if db_path is not None else CHECKPOINT_DB_PATH
    if not target_path.exists():
        return []

    try:
        with sqlite3.connect(str(target_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints';"
            )
            if not cursor.fetchone():
                return []
            cursor.execute(
                "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id != '' ORDER BY thread_id;"
            )
            return [row[0] for row in cursor.fetchall()]
    except (sqlite3.Error, OSError):
        return []


def _handle_command(input_query: str, config: dict, db_path: Path | str | None = None, store: BaseStore | None = None) -> bool:
    """Handle slash commands. Returns True if handled, False otherwise."""
    parts = input_query.strip().split()
    cmd = parts[0].lower()

    if cmd == "/help":
        print(f"\n{BOLD}Available commands:{RESET}")
        print(f"  {CYAN}/help{RESET}                - Show this help message")
        print(f"  {CYAN}/models{RESET}              - Show available models")
        print(f"  {CYAN}/switch <model>{RESET}      - Switch to a different model")
        print(f"  {CYAN}/thread{RESET}              - Show current thread ID")
        print(f"  {CYAN}/threads{RESET}             - List all saved threads")
        print(f"  {CYAN}/new [thread_id]{RESET}      - Start a new conversation thread")
        print(f"  {CYAN}/switch-thread <id>{RESET}  - Switch to an existing thread")
        print(f"  {CYAN}/list-memories{RESET}        - List all memories")
        print(f"  {CYAN}/clear-memories{RESET}       - Clear all memories")
        print(f"  {CYAN}/delete-memory <id>{RESET}    - Delete a memory")
        print(f"  {CYAN}/exit{RESET}                - Exit the chat\n")
        return True

    elif cmd == "/models":
        print(f"\n{BOLD}Available models:{RESET}")
        for key, val in settings.models.items():
            current_marker = f" {GREEN}(current){RESET}" if key == settings.current_model or val == settings.current_model else ""
            print(f"  - {CYAN}{key}{RESET} -> {val}{current_marker}")
        print()
        return True

    elif cmd == "/switch":
        if len(parts) < 2:
            print(f"{YELLOW}Usage: /switch <model_name>{RESET}")
            print(f"Available: {', '.join(settings.models.keys())}\n")
            return True

        model_name = parts[1]
        try:
            set_current_model(model_name)
            config["configurable"]["model"] = settings.current_model
            print(f"{GREEN}✓ Switched to model: {model_name} ({settings.current_model}){RESET}\n")
        except ValueError:
            print(f"{YELLOW}Error: Model '{model_name}' not found.{RESET}")
            print(f"Available: {', '.join(settings.models.keys())}\n")
        return True

    elif cmd == "/thread":
        current_thread = config.get("configurable", {}).get("thread_id", "-")
        print(f"\n{CYAN}Current Thread ID:{RESET} {BOLD}{current_thread}{RESET}\n")
        return True

    elif cmd in ("/threads", "/all-threads"):
        threads = get_all_threads(db_path)
        current_thread = config.get("configurable", {}).get("thread_id", "-")
        print(f"\n{BOLD}Saved threads:{RESET}")
        if not threads:
            print(f"  {DIM}(No saved threads found){RESET}")
        else:
            for tid in threads:
                current_marker = f" {GREEN}(current){RESET}" if tid == current_thread else ""
                print(f"  - {CYAN}{tid}{RESET}{current_marker}")
        if current_thread != "-" and current_thread not in threads:
            print(f"\n{DIM}Current unsaved session:{RESET} {CYAN}{current_thread}{RESET} {GREEN}(current){RESET}")
        print()
        return True

    elif cmd == "/new":
        if len(parts) > 1:
            new_thread = parts[1]
        else:
            new_thread = f"session-{uuid.uuid4().hex[:8]}"
        config.setdefault("configurable", {})["thread_id"] = new_thread
        print(f"\n{GREEN}✓ Started new thread:{RESET} {BOLD}{new_thread}{RESET}\n")
        return True

    elif cmd == "/switch-thread":
        if len(parts) < 2:
            print(f"{YELLOW}Usage: /switch-thread <thread_id>{RESET}\n")
            return True
        target_thread = parts[1]
        config.setdefault("configurable", {})["thread_id"] = target_thread
        print(f"\n{GREEN}✓ Switched to thread:{RESET} {BOLD}{target_thread}{RESET}\n")
        return True

    elif cmd == "/list-memories":
        memories = get_all_memories(store)
        print(f"\n{BOLD}Memories:{RESET}")
        if not memories:
            print(f"  {DIM}(No memories found){RESET}")
        else:
            for memory in memories:
                print(f"  - {CYAN}{memory}{RESET}")
        print()
        return True

    elif cmd == "/clear-memories":
        clear_memories(store)
        print(f"\n{GREEN}✓ Cleared all memories{RESET}\n")
        return True

    elif cmd == "/delete-memory":
        if len(parts) < 2:
            print(f"{YELLOW}Usage: /delete-memory <memory_id>{RESET}\n")
            return True
        memory_id = parts[1]
        delete_memory(memory_id, store)
        print(f"\n{GREEN}✓ Deleted memory:{RESET} {BOLD}{memory_id}{RESET}\n")
        return True

    elif cmd in ("/exit", "/quit"):
        return False 

    else:
        print(f"{YELLOW}Unknown command '{cmd}'. Type /help to see available commands.{RESET}\n")
        return True


def _extract_chunk_text(chunk) -> str:
    """Extract plain text from a streaming chunk across different providers."""
    if not chunk:
        return ""
    if hasattr(chunk, "text") and chunk.text:
        return str(chunk.text)
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "".join(parts)
    return ""


async def main(thread_id: str | None = None, db_path: Path | str | None = None, store_path: Path | str | None = None):

    # Load tools early and fall back gracefully
    # This enables, if tool loading fails, the CLI can still start the normal chat without tools
    try:
        mcp_tools = get_tools_sync()
    except Exception as exc: # noqa: BLE001
        print(f"Warning: MCP tools unavailable: {exc}")
        mcp_tools = []
    list_of_tools = [*memory_tools, *mcp_tools]

    active_chkpt_db_path = Path(db_path) if db_path is not None else CHECKPOINT_DB_PATH
    active_store_db_path = Path(store_path) if store_path is not None else STORE_DB_PATH

    active_chkpt_db_path.parent.mkdir(parents=True, exist_ok=True)
    active_store_db_path.parent.mkdir(parents=True, exist_ok=True)

    active_thread = str(thread_id) if thread_id else f"session-{uuid.uuid4().hex[:8]}"

    with SqliteStore.from_conn_string(str(active_store_db_path)) as store:
        store.setup()
        async with AsyncSqliteSaver.from_conn_string(str(active_chkpt_db_path)) as checkpointer:
            CONFIG = {"configurable": {"thread_id": active_thread, "model": settings.current_model}}
            graph = build_graph(tools=list_of_tools, checkpointer=checkpointer, store=store)
            
            print(
                f"{BOLD}ChatBot CLI ready!{RESET} (Thread: {CYAN}{active_thread}{RESET})\n"
                f"Type {CYAN}/help{RESET} for commands or {CYAN}/exit{RESET} to quit.\n"
            )
            
            while True:
                try:
                    raw_input = input("You: ")
                except (KeyboardInterrupt, EOFError):
                    print("\nExiting chat...")
                    break

                user_query = raw_input.strip()
                if not user_query:
                    continue

                if user_query.lower() in ("/exit", "/quit", "exit", "quit"):
                    print("Goodbye! 👋")
                    break

                if user_query.startswith("/"):
                    _handle_command(user_query, CONFIG, db_path=active_chkpt_db_path, store=store)
                    continue

                start_time = time.perf_counter()
                current_model_info = {}
                assistant_started = False
                print("\n" + "─" * 60)
                async for event in graph.astream_events(input={"messages": [HumanMessage(content=user_query)]}, config=CONFIG, version="v2"):
                    kind = event["event"]
                    name = event.get("name", "")
                    meta = event.get("metadata", {})
                    data = event.get("data", {})

                    if kind == "on_chain_start":
                        if name == "LangGraph":
                            thread_id = CONFIG.get("configurable", {}).get("thread_id", "-")
                            print(f"{DIM}[Graph] Started (thread_id: {thread_id}){RESET}")
                        else:
                            print(f"{CYAN}[Node: {name}]{RESET} Started")

                    elif kind == "on_chat_model_start":
                        current_model_info = {
                            "model_name": meta.get("ls_model_name", "LLM"),
                            "provider": meta.get("ls_provider", ""),
                            "temp": meta.get("ls_temperature", ""),
                        }
                        assistant_started = False

                    elif kind == "on_chat_model_stream":
                        chunk = data.get("chunk")
                        text = _extract_chunk_text(chunk)
                        if text:
                            if not assistant_started:
                                print(f"{BOLD}Assistant:{RESET} ", end="", flush=True)
                                assistant_started = True
                            print(text, end="", flush=True)

                    elif kind == "on_chat_model_end":
                        if assistant_started:
                            print() 
                        output = data.get("output")
                        usage = getattr(output, "usage_metadata", {}) or {}
                        resp_meta = getattr(output, "response_metadata", {}) or {}

                        model_name = resp_meta.get("model_name") or current_model_info.get("model_name", "LLM")
                        provider = current_model_info.get("provider") or resp_meta.get("model_provider", "")
                        temp = current_model_info.get("temp", "")
                        finish = resp_meta.get("finish_reason", "completed")

                        provider_str = f" ({provider})" if provider else ""
                        temp_str = f" | temp: {temp}" if temp != "" else ""
                        p_tokens = usage.get("input_tokens", "-")
                        c_tokens = usage.get("output_tokens", "-")
                        t_tokens = usage.get("total_tokens", "-")

                        print(
                            f"{DIM}[Model Stats] {model_name}{provider_str}{temp_str} | "
                            f"tokens: prompt={p_tokens}, completion={c_tokens}, total={t_tokens} | "
                            f"finish: {finish}{RESET}"
                        )

                    elif kind == "on_tool_start":
                        tool_input = data.get("input", "")
                        print(f"\n{YELLOW}[Tool: {name}] Input:{RESET} {tool_input}")

                    elif kind == "on_tool_end":
                        tool_out = data.get("output", "")
                        if hasattr(tool_out, "text") and tool_out.text:
                            tool_output = tool_out.text
                        elif hasattr(tool_out, "content") and tool_out.content:
                            tool_output = tool_out.content
                        else:
                            tool_output = str(tool_out) if tool_out else ""
                        print(f"{YELLOW}[Tool: {name}] Output:{RESET} {tool_output}")

                    elif kind == "on_chain_end":
                        if name == "LangGraph":
                            elapsed = time.perf_counter() - start_time
                            print(f"{DIM}[Graph] Finished in {elapsed:.2f}s{RESET}")
                            print("─" * 60 + "\n")
                        else:
                            print(f"{CYAN}[Node: {name}]{RESET} Completed")

    
if __name__ == "__main__":
    asyncio.run(main())
