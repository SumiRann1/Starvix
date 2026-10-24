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
def search_memory(
    query: str,
    *,
    store: Annotated[BaseStore, InjectedStore()],
    limit: int = 5,
):
    """Search the knowledge base for facts or preferences about the user (bounded to top 5-10 results)."""
    bounded_limit = min(max(1, limit), 10)
    items = store.search(NAMESPACE, query=query, limit=bounded_limit)
    if not items:
        return "No matching memories found."
    return "\n".join([f"- [{item.key}] {item.value.get('fact', '')}" for item in items])


def delete_memory(memory_id: str, store: BaseStore | None = None) -> bool:
    """Delete a memory by its ID."""
    if store is None or not memory_id:
        return False
    store.delete(NAMESPACE, key=memory_id)
    return True


def get_all_memories(
    store: BaseStore | None = None, limit: int | None = None
) -> list[str]:
    """Retrieve all saved memories as formatted strings."""
    if store is None:
        return []
    if limit is not None:
        items = store.search(NAMESPACE, limit=limit)
        return [f"[{item.key}] {item.value.get('fact', '')}" for item in items]

    all_items = []
    offset = 0
    batch_size = 100
    while True:
        batch = store.search(NAMESPACE, limit=batch_size, offset=offset)
        if not batch:
            break
        all_items.extend(batch)
        if len(batch) < batch_size:
            break
        offset += len(batch)

    return [f"[{item.key}] {item.value.get('fact', '')}" for item in all_items]


def clear_memories(store: BaseStore | None = None) -> bool:
    """Clear all memories in the namespace."""
    if store is None:
        return False
    while True:
        items = store.search(NAMESPACE, limit=100)
        if not items:
            break
        for item in items:
            store.delete(NAMESPACE, key=item.key)
    return True


memory_tools = [save_memory, search_memory]
