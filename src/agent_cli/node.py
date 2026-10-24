from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from .config import settings
from .guardrails import check_input, sanitize_output
from .models import get_model
from .state import SYSTEM_PROMPT, AgentState


def make_chat_node(tools: list | None = None):
    """Factory that creates a chat node with tools bound to the model."""

    def chat_node(state: AgentState, config: RunnableConfig | None = None):
        history = [
            message
            for message in state.get("messages", [])
            if not isinstance(message, SystemMessage)
        ]

        # Guardrails Input validation: check for prompt injection on the most recent human message
        if history and getattr(history[-1], "type", None) == "human":
            human_content = history[-1].content
            if isinstance(human_content, str):
                try:
                    check_input(human_content)
                except ValueError as err:
                    return {
                        "messages": [
                            AIMessage(
                                content=f"Security Refusal: {err}. Your prompt was flagged by Guardrails and cannot be processed."
                            )
                        ]
                    }

        configurable = config.get("configurable", {}) if config else {}
        model_id = configurable.get("model") or settings.current_model
        model = get_model(model_id)

        # Configurable tools take precedence if explicitly provided; otherwise use tools from factory
        node_tools = configurable.get("tools") if "tools" in configurable else tools
        if node_tools and hasattr(model, "bind_tools"):
            model = model.bind_tools(node_tools)

        model_messages = [SystemMessage(content=SYSTEM_PROMPT), *history]
        result = model.invoke(model_messages)

        # Guardrails Output validation: redact secrets and API keys from model response
        if hasattr(result, "content") and isinstance(result.content, str):
            result.content = sanitize_output(result.content)

        return {"messages": [result]}

    return chat_node


# Default chat node instance (without pre-bound tools)
chat_node = make_chat_node()
