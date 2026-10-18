"""Agent CLI package."""

__version__ = "0.1.0"

from .config import set_current_model, settings
from .graph import build_graph
from .models import get_model, list_models
from .node import chat_node, make_chat_node
from .state import SYSTEM_PROMPT, AgentState
from .tool import client, get_tools, get_tools_sync

__all__ = [
    "SYSTEM_PROMPT",
    "AgentState",
    "__version__",
    "build_graph",
    "chat_node",
    "client",
    "get_model",
    "get_tools",
    "get_tools_sync",
    "list_models",
    "make_chat_node",
    "set_current_model",
    "settings",
]