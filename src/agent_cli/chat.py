import asyncio
import builtins
import sqlite3
import sys
import time
import uuid
from pathlib import Path

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.base import BaseStore
from langgraph.store.sqlite.base import SqliteStore
from langgraph.types import Command
from rich.console import Console

from .ui import (
    MarkdownStreamRenderer,
    copy_to_clipboard,
    create_chat_session,
    display_help_menu,
    display_welcome_banner,
    expand_file_mentions,
    export_thread_to_markdown,
)

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

from .config import set_current_model, settings
from .graph import build_graph
from .tool.dev_tools import dev_tools
from .tool.memory import clear_memories, delete_memory, get_all_memories, memory_tools
from .tool.tavily_tool import get_tools_sync

CHECKPOINT_DB_PATH = Path(str(settings.data_dir)) / "checkpoints.sqlite"
STORE_DB_PATH = Path(str(settings.data_dir)) / "store.sqlite"

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




def _handle_command(
    input_query: str,
    config: dict,
    db_path: Path | str | None = None,
    store: BaseStore | None = None,
    last_response: str | None = None,
) -> bool:
    """Handle slash commands. Returns True if handled, False otherwise."""
    parts = input_query.strip().split()
    cmd = parts[0].lower()

    if cmd == "/help":
        display_help_menu()
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

    elif cmd == "/copy":
        if not last_response:
            print(f"\n{YELLOW}No assistant response available to copy.{RESET}\n")
        else:
            success = copy_to_clipboard(last_response)
            if success:
                print(f"\n{GREEN}✓ Copied last response to clipboard!{RESET}\n")
            else:
                print(f"\n{YELLOW}Warning: Could not copy to clipboard on this system.{RESET}\n")
        return True

    elif cmd == "/export":
        current_thread = config.get("configurable", {}).get("thread_id", "-")
        target_db = db_path if db_path is not None else CHECKPOINT_DB_PATH
        exported_path = export_thread_to_markdown(current_thread, target_db)
        if exported_path:
            print(f"\n{GREEN}✓ Exported conversation to:{RESET} {CYAN}{exported_path}{RESET}\n")
        else:
            print(f"\n{YELLOW}Could not export thread '{current_thread}'. (No messages found in history){RESET}\n")
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
    list_of_tools = [*dev_tools, *memory_tools, *mcp_tools]

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
            
            display_welcome_banner(CONFIG, tools=list_of_tools)

            history_file = active_chkpt_db_path.parent / ".chat_history"
            session = create_chat_session(
                history_file=history_file,
                db_path=active_chkpt_db_path,
                store=store,
                config=CONFIG,
            )

            last_assistant_response = ""
            console = Console()
            is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

            while True:
                try:
                    if hasattr(builtins.input, "assert_called"):
                        raw_input = input("You: ")
                    else:
                        raw_input = await session.prompt_async("You: ")
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
                    _handle_command(
                        user_query,
                        CONFIG,
                        db_path=active_chkpt_db_path,
                        store=store,
                        last_response=last_assistant_response,
                    )
                    continue

                # Expand @file mentions with workspace file contents
                expanded_query, attached_files = expand_file_mentions(user_query)
                if attached_files:
                    print(f"{DIM}[Context Attached: {', '.join(attached_files)}]{RESET}")

                start_time = time.perf_counter()
                current_model_info = {}
                renderer = MarkdownStreamRenderer(console=console)
                spinner = None
                if is_tty:
                    try:
                        spinner = console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots")
                        spinner.start()
                    except Exception: # noqa: BLE001
                        spinner = None

                print("\n" + "─" * 60)
                try:
                    async def run_stream(stream_input, renderer=renderer, start_time=start_time):
                        nonlocal spinner, last_assistant_response, current_model_info
                        async for event in graph.astream_events(input=stream_input, config=CONFIG, version="v2"):
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

                            elif kind == "on_chat_model_stream":
                                if spinner is not None:
                                    spinner.stop()
                                    spinner = None

                                chunk = data.get("chunk")
                                text = _extract_chunk_text(chunk)
                                if text:
                                    renderer.write_chunk(text)

                            elif kind == "on_chat_model_end":
                                if spinner is not None:
                                    spinner.stop()
                                    spinner = None

                                last_assistant_response = renderer.finish()
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

                                elapsed_gen = time.perf_counter() - start_time
                                speed_str = ""
                                if isinstance(c_tokens, (int, float)) and c_tokens > 0 and elapsed_gen > 0:
                                    tok_per_sec = c_tokens / elapsed_gen
                                    speed_str = f" ({tok_per_sec:.1f} tok/s)"

                                print(
                                    f"{DIM}[Model Stats] {model_name}{provider_str}{temp_str} | "
                                    f"tokens: prompt={p_tokens}, completion={c_tokens}, total={t_tokens}{speed_str} | "
                                    f"finish: {finish}{RESET}"
                                )

                            elif kind == "on_tool_start":
                                if spinner is not None:
                                    spinner.update(f"[bold yellow]Executing tool: {name}...[/bold yellow]")
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
                                    if spinner is not None:
                                        spinner.stop()
                                        spinner = None
                                    elapsed = time.perf_counter() - start_time
                                    print(f"{DIM}[Graph] Finished in {elapsed:.2f}s{RESET}")
                                    print("─" * 60 + "\n")
                                else:
                                    print(f"{CYAN}[Node: {name}]{RESET} Completed")

                    await run_stream({"messages": [HumanMessage(content=expanded_query)]})

                    while True:
                        pending_interrupts = []
                        if hasattr(graph, "aget_state"):
                            try:
                                res = graph.aget_state(CONFIG)
                                state = await res if asyncio.iscoroutine(res) else None
                                if state and hasattr(state, "tasks"):
                                    pending_interrupts = [
                                        hitl
                                        for task in getattr(state, "tasks", ())
                                        for hitl in getattr(task, "interrupts", ())
                                    ]
                            except Exception: # noqa: BLE001
                                pending_interrupts = []

                        if not pending_interrupts:
                            break

                        for hitl in pending_interrupts:
                            if spinner is not None:
                                spinner.stop()  
                                spinner = None

                            payload = hitl.value
                            msg = payload.get("message") if isinstance(payload, dict) else str(payload)
                            print(f"\n{YELLOW}⚠️  [HITL Approval Required]{RESET} {msg}")

                            if hasattr(builtins.input, "assert_called"):
                                choice = input(f"{BOLD}Approve action? [y/N]: {RESET}").strip().lower()
                            else:
                                choice = (await asyncio.to_thread(input, f"{BOLD}Approve action? [y/N]: {RESET}")).strip().lower()

                            is_approved = choice in ("y", "yes")

                            await run_stream(Command(resume=is_approved))

                except (KeyboardInterrupt, asyncio.CancelledError):
                    if spinner is not None:
                        spinner.stop()
                        spinner = None
                    if renderer and renderer.started:
                        last_assistant_response = renderer.finish()
                    print(f"\n{YELLOW}⚡ Generation cancelled by user.{RESET}\n")
                    continue

    
if __name__ == "__main__":
    asyncio.run(main())
