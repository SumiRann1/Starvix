from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from .config import settings
from .models import get_model
from .state import SYSTEM_PROMPT, AgentState


def make_chat_node(tools: list | None = None):
    """Factory that creates a chat node with tools bound to the model."""
    def chat_node(state: AgentState, config: RunnableConfig | None = None):
        configurable = config.get("configurable", {}) if config else {}
        model_id = configurable.get("model") or settings.current_model
        model = get_model(model_id)

        # Configurable tools take precedence if explicitly provided; otherwise use tools from factory
        node_tools = configurable.get("tools") if "tools" in configurable else tools
        if node_tools and hasattr(model, "bind_tools"):
            model = model.bind_tools(node_tools)

        history = [
            message
            for message in state.get("messages", [])
            if not isinstance(message, SystemMessage)
        ]

        model_messages = [SystemMessage(content=SYSTEM_PROMPT), *history]
        result = model.invoke(model_messages)
        return {"messages": [result]}

    return chat_node


# Default chat node instance (without pre-bound tools)
chat_node = make_chat_node()
    

    
