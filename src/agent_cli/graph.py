import asyncio
import logging

from langchain_core.tools import ToolException
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.memory import InMemoryStore

from .node import make_chat_node
from .state import AgentState
from .tool.dev_tools import dev_tools
from .tool.memory import memory_tools

logger = logging.getLogger("agent_cli.tools")

# Whitelist of domain/runtime exceptions that tools legitimately raise
EXPECTED_TOOL_EXCEPTIONS = (
    ToolException,
    ValueError,
    FileNotFoundError,
    PermissionError,
    IsADirectoryError,
    NotADirectoryError,
    TimeoutError,
    OSError,
)

HandledToolErrors = (
    ToolException
    | ValueError
    | FileNotFoundError
    | PermissionError
    | IsADirectoryError
    | NotADirectoryError
    | TimeoutError
    | OSError
)


def custom_error_handler(error: HandledToolErrors) -> str:
    # 1. Do not swallow critical system or cancellation interrupts
    if isinstance(
        error, (KeyboardInterrupt, SystemExit, asyncio.CancelledError, BaseException)
    ) and not isinstance(error, Exception):
        raise error

    # 2. Unexpected developer bugs (AttributeError, RuntimeError, NameError, etc.) must propagate
    if not isinstance(error, EXPECTED_TOOL_EXCEPTIONS):
        raise error

    error_type = type(error).__name__
    error_str = str(error).strip() or repr(error)
    logger.warning(f"Tool execution failed: {error_type} - {error_str}", exc_info=error)

    # 3. Truncate long error outputs to protect context window
    if len(error_str) > 600:
        error_str = error_str[:600] + "... [truncated]"

    # 4. Context-aware guidance for LLM recovery
    guidance = "Please review your arguments and try again."
    if isinstance(error, FileNotFoundError):
        guidance = "The specified file/path was not found. Consider listing the directory first to verify the path."
    elif isinstance(error, PermissionError):
        guidance = (
            "Permission denied for this resource. Try an alternative file or approach."
        )
    elif isinstance(error, TimeoutError):
        guidance = "The operation timed out. Please try a simpler or faster query."
    elif isinstance(error, (ValueError, ToolException)):
        guidance = "Input argument mismatch or invalid values provided. Please inspect the tool schema."

    return (
        f"Tool Execution Failed [{error_type}]:\n"
        f"Details: {error_str}\n"
        f"Instruction: {guidance}"
    )


def build_graph(state=AgentState, tools=None, checkpointer=None, store=None):
    # Agar tools diye nahi gayenge toh default tools use honge iski wajah se error aa rahi thi
    if tools is None:
        tools = dev_tools + memory_tools

    toolnode = ToolNode(tools, handle_tool_errors=custom_error_handler)

    graph_builder = StateGraph(state)

    # Ab chat node banega tools ke saath
    chat_node_instance = make_chat_node(tools)
    graph_builder.add_node("chat", chat_node_instance)

    graph_builder.add_node("tools", toolnode)

    graph_builder.add_edge(START, "chat")
    graph_builder.add_conditional_edges("chat", tools_condition)
    graph_builder.add_edge("tools", "chat")

    if checkpointer is None:
        checkpointer = MemorySaver()
    if store is None:
        store = InMemoryStore()

    return graph_builder.compile(checkpointer=checkpointer, store=store)
