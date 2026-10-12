from pathlib import Path
import sys
import asyncio
import time
from langchain_core.messages import HumanMessage

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT))

from agent_cli import AgentState, build_graph, settings, set_current_model


def _handle_command(input_query: str, config: dict) -> bool:
    """Handle slash commands. Returns True if handled, False otherwise."""
    parts = input_query.strip().split()
    cmd = parts[0].lower()

    if cmd == "/help":
        print(f"\n{BOLD}Available commands:{RESET}")
        print(f"  {CYAN}/help{RESET}           - Show this help message")
        print(f"  {CYAN}/models{RESET}         - Show available models")
        print(f"  {CYAN}/switch <model>{RESET} - Switch to a different model")
        print(f"  {CYAN}/exit{RESET}           - Exit the chat\n")
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

    elif cmd in ("/exit", "/quit"):
        return False 

    else:
        print(f"{YELLOW}Unknown command '{cmd}'. Type /help to see available commands.{RESET}\n")
        return True


async def main():
    CONFIG = {"configurable": {"thread_id": 1, "model": settings.current_model}}
    graph = build_graph()
    
    print(f"{BOLD}ChatBot CLI ready!{RESET} Type {CYAN}/help{RESET} for commands or {CYAN}/exit{RESET} to quit.\n")
    
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
            _handle_command(user_query, CONFIG)
            continue

        start_time = time.perf_counter()
        current_model_info = {}
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
                print(f"{BOLD}Assistant:{RESET} ", end="", flush=True)

            elif kind == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk and chunk.content:
                    print(chunk.content, end="", flush=True)

            elif kind == "on_chat_model_end":
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
                tool_output = data.get("output", "")
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
