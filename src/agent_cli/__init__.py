"""Agent CLI package."""

__version__ = "0.1.0"

from .config import set_current_model, settings
from .graph import build_graph
from .models import get_model, list_models
from .node import chat_node
from .state import AgentState, SYSTEM_PROMPT

__all__ = [
    "__version__",
    "AgentState",
    "SYSTEM_PROMPT",
    "build_graph",
    "chat_node",
    "get_model",
    "list_models",
    "set_current_model",
    "settings",
]