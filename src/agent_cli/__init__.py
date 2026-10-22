"""Agent CLI package."""

__version__ = "0.1.0"

from .chat import get_all_threads
from .config import set_current_model, settings
from .graph import build_graph
from .memory import clear_memories, delete_memory, get_all_memories, memory_tools
from .models import get_model, list_models
from .node import chat_node, make_chat_node
from .state import SYSTEM_PROMPT, AgentState

__all__ = [
    "SYSTEM_PROMPT",
    "AgentState",
    "__version__",
    "build_graph",
    "chat_node",
    "clear_memories",
    "client",
    "delete_memory",
    "get_all_memories",
    "get_all_threads",
    "get_model",
    "get_tools",
    "get_tools_sync",
    "list_models",
    "make_chat_node",
    "memory_tools",
    "set_current_model",
    "settings",
]