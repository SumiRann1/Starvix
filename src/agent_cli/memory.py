import uuid
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore

NAMESPACE = ("memories", "default")


@tool
def save_memory(fact: str, *, store: Annotated[BaseStore, InjectedStore()]):
    """Save an important fact or preference about the user across conversations."""
    memory_id = uuid.uuid4().hex[:8]
    store.put(NAMESPACE, key=memory_id, value={"fact": fact})
    return f"Saved memory [{memory_id}]: {fact}"


@tool
def search_memory(query: str, *, store: Annotated[BaseStore, InjectedStore()]):
    """Search the knowledge base for facts or preferences about the user."""
    items = store.search(NAMESPACE, query=query)
    if not items:
        return "No matching memories found."
    return "\n".join([f"- [{item.key}] {item.value.get('fact', '')}" for item in items])


def delete_memory(memory_id: str, store: BaseStore | None = None) -> bool:
    """Delete a memory by its ID."""
    if store is None or not memory_id:
        return False
    store.delete(NAMESPACE, key=memory_id)
    return True


def get_all_memories(store: BaseStore | None = None) -> list[str]:
    """Retrieve all saved memories as formatted strings."""
    if store is None:
        return []
    items = store.search(NAMESPACE)
    return [f"[{item.key}] {item.value.get('fact', '')}" for item in items]


def clear_memories(store: BaseStore | None = None) -> bool:
    """Clear all memories in the namespace."""
    if store is None:
        return False
    for item in store.search(NAMESPACE):
        store.delete(NAMESPACE, key=item.key)
    return True


memory_tools = [save_memory, search_memory]
