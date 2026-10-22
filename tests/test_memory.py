import pytest
from langchain_core.messages import AIMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.memory import InMemoryStore
from langgraph.store.sqlite.base import SqliteStore

from agent_cli.graph import build_graph
from agent_cli.memory import (
    NAMESPACE,
    clear_memories,
    delete_memory,
    get_all_memories,
    memory_tools,
    save_memory,
    search_memory,
)
from agent_cli.state import AgentState


def test_get_all_memories_none_store():
    """Verify get_all_memories returns an empty list when store is None."""
    assert get_all_memories(None) == []


def test_delete_memory_none_store_or_empty_id():
    """Verify delete_memory returns False when store is None or ID is empty."""
    assert delete_memory("123", None) is False
    store = InMemoryStore()
    assert delete_memory("", store) is False


def test_clear_memories_none_store():
    """Verify clear_memories returns False when store is None."""
    assert clear_memories(None) is False


def test_save_and_search_memory_tool_invocation():
    """Verify save_memory and search_memory tools work via direct invocation."""
    store = InMemoryStore()

    # Invoke save_memory
    save_res = save_memory.invoke({"fact": "User prefers dark mode", "store": store})
    assert "Saved memory" in save_res
    assert "User prefers dark mode" in save_res

    # Check store content
    memories = get_all_memories(store)
    assert len(memories) == 1
    assert "User prefers dark mode" in memories[0]

    # Invoke search_memory
    search_res = search_memory.invoke({"query": "dark mode", "store": store})
    assert "User prefers dark mode" in search_res


def test_search_memory_no_results():
    """Verify search_memory returns a fallback message when no memories match."""
    store = InMemoryStore()
    search_res = search_memory.invoke({"query": "non_existent_topic", "store": store})
    assert search_res == "No matching memories found."


def test_graph_tool_execution_with_store():
    """Verify ToolNode in a compiled StateGraph injects store into save_memory."""
    store = InMemoryStore()
    builder = StateGraph(AgentState)
    builder.add_node("tools", ToolNode([save_memory]))
    builder.add_edge(START, "tools")
    graph = builder.compile(store=store)

    ai_msg = AIMessage(
        content="",
        tool_calls=[{"name": "save_memory", "args": {"fact": "Graph injected fact"}, "id": "call_1"}],
    )
    result = graph.invoke({"messages": [ai_msg]})
    assert any("Graph injected fact" in m.content for m in result["messages"])

    all_mems = get_all_memories(store)
    assert len(all_mems) == 1
    assert "Graph injected fact" in all_mems[0]


def test_delete_and_clear_memories():
    """Verify deleting a specific memory and clearing all memories."""
    store = InMemoryStore()
    for i in range(100):
        store.put(NAMESPACE, key=f"mem-{i}", value={"fact": f"Fact {i}"})
    assert len(get_all_memories(store)) == 100
    # Delete single memory
    deleted = delete_memory("mem-50", store)
    assert deleted is True
    remaining = get_all_memories(store)
    assert len(remaining) == 99
    assert "Fact 50" not in remaining[0]

    # Clear all memories
    cleared = clear_memories(store)
    assert cleared is True
    assert get_all_memories(store) == []


def test_sqlite_store_persistence_across_sessions(tmp_path):
    """Verify memories persist to SQLite disk storage across independent store sessions."""
    db_file = tmp_path / "ltm_persistence.sqlite"

    # Session 1: Put memory into persistent store and close
    with SqliteStore.from_conn_string(str(db_file)) as store_1:
        store_1.setup()
        store_1.put(NAMESPACE, key="persisted-1", value={"fact": "Persistent Fact across sessions"})

    # Session 2: Open a fresh SqliteStore instance from the same file
    with SqliteStore.from_conn_string(str(db_file)) as store_2:
        store_2.setup()
        all_memories = get_all_memories(store_2)
        assert len(all_memories) == 1
        assert "Persistent Fact across sessions" in all_memories[0]
        assert "[persisted-1]" in all_memories[0]


def test_build_graph_with_custom_store():
    """Verify build_graph registers the provided store onto the compiled graph."""
    store = InMemoryStore()
    graph = build_graph(tools=memory_tools, store=store)
    assert graph.store is store


def test_search_memory_bounded_limit():
    """Verify search_memory bounds results to 5 by default and caps at 10."""
    store = InMemoryStore()
    for i in range(20):
        store.put(NAMESPACE, key=f"pref-{i}", value={"fact": f"User preference number {i}"})

    # Default invocation returns 5 results
    res_default = search_memory.invoke({"query": "preference", "store": store})
    lines_default = [line for line in res_default.split("\n") if line.strip()]
    assert len(lines_default) == 5

    # Limit of 100 is capped to 10 to protect context window
    res_capped = search_memory.invoke({"query": "preference", "store": store, "limit": 100})
    lines_capped = [line for line in res_capped.split("\n") if line.strip()]
    assert len(lines_capped) == 10

