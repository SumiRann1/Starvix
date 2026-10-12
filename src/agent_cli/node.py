from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from .config import settings
from .models import get_model
from .state import AgentState, SYSTEM_PROMPT


def chat_node(state: AgentState, config: RunnableConfig | None = None):
    configurable = config.get("configurable", {}) if config else {}
    model_id = configurable.get("model") or settings.current_model
    model = get_model(model_id)
    messages = list(state.get("messages", []))

    history = [message for message in state.get("messages", [])
                    if not isinstance(message, SystemMessage)]
    
    model_messages = [SystemMessage(content=SYSTEM_PROMPT), *history]
    result = model.invoke(model_messages)
    return {"messages": [result]}

    
