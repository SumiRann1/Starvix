from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


SYSTEM_PROMPT = """You are a helpful assistant.
You have access to long-term memory tools (save_memory, search_memory).
- When the user shares personal details, preferences, or important instructions, use `save_memory` to remember them.
- When answering queries where past user context might be relevant, use `search_memory` first.
"""
