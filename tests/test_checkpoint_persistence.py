from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent_cli.chat import get_all_threads
from agent_cli.graph import build_graph


@tool
def sample_tool(query: str) -> str:
    """A sample tool for persistence tests."""
    return f"processed: {query}"


def test_build_graph_defaults_to_memory_saver():
    """Yeh test check karta hai ki agar checkpointer provide na kiya jaye, toh build_graph by default MemorySaver use kare."""
    graph = build_graph(tools=[])
    assert graph.checkpointer is not None
    assert isinstance(graph.checkpointer, MemorySaver)


@pytest.mark.anyio
async def test_build_graph_uses_provided_async_checkpointer(tmp_path):
    """Yeh test verify karta hai ki agar hum explicitly AsyncSqliteSaver dein, toh graph wahi checkpointer use kare."""
    db_path = tmp_path / "custom_async.sqlite"
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(tools=[], checkpointer=checkpointer)
        assert graph.checkpointer is checkpointer
        assert isinstance(graph.checkpointer, AsyncSqliteSaver)


@pytest.mark.anyio
async def test_async_sqlite_checkpointer_setup_idempotent(tmp_path):
    """Yeh test check karta hai ki checkpointer.setup() ko multiple times call karne par bhi koi error na aaye (idempotent rahe)."""
    db_path = tmp_path / "idempotent_async.sqlite"
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        # Pehli baar setup schema banayega
        await checkpointer.setup()
        # Dusri baar call karne par safely pass hona chahiye
        await checkpointer.setup()


@pytest.mark.anyio
async def test_async_sqlite_persistence_across_sessions(tmp_path):
    """Yeh test check karta hai ki CLI session band hone aur dubara naye graph instance ke sath start hone par bhi SQLite se purani chat history restore ho jaye."""
    db_path = tmp_path / "async_sessions.sqlite"
    thread_id = "thread-persistence-test"
    config = {
        "configurable": {
            "thread_id": thread_id,
            "model": "test-model",
            "tools": [],
        }
    }

    # Session 1: Pehla message bhejo, SQLite mein save karo aur session band karo
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer1:
        graph1 = build_graph(tools=[], checkpointer=checkpointer1)

        fake_model1 = Mock()
        fake_model1.bind_tools.return_value = fake_model1
        fake_model1.invoke.return_value = AIMessage(
            content="Hello Alice, nice to meet you!"
        )

        with patch("agent_cli.node.get_model", return_value=fake_model1):
            result1 = await graph1.ainvoke(
                {"messages": [HumanMessage(content="My name is Alice")]},
                config=config,
            )

        assert result1["messages"][-1].content == "Hello Alice, nice to meet you!"

    # Session 2: Connect anew to the same SQLite file in a fresh graph instance
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer2:
        graph2 = build_graph(tools=[], checkpointer=checkpointer2)

        fake_model2 = Mock()
        fake_model2.bind_tools.return_value = fake_model2
        fake_model2.invoke.return_value = AIMessage(content="Your name is Alice.")

        with patch("agent_cli.node.get_model", return_value=fake_model2):
            result2 = await graph2.ainvoke(
                {"messages": [HumanMessage(content="What is my name?")]},
                config=config,
            )

        assert result2["messages"][-1].content == "Your name is Alice."

        # Model ko session 2 mein SQLite checkpoint se purani history mili ya nahi, yeh verify karo
        call_messages = fake_model2.invoke.call_args.args[0]
        history_contents = [getattr(m, "content", "") for m in call_messages]

        assert any("My name is Alice" in c for c in history_contents)
        assert any("Hello Alice, nice to meet you!" in c for c in history_contents)
        assert any("What is my name?" in c for c in history_contents)


@pytest.mark.anyio
async def test_async_sqlite_checkpointer_thread_isolation(tmp_path):
    """Yeh test ensure karta hai ki do alag-alag thread_ids ka data ek dusre mein leak na ho aur proper isolation rahe."""
    db_path = tmp_path / "async_isolation.sqlite"
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(tools=[], checkpointer=checkpointer)

        fake_model = Mock()
        fake_model.bind_tools.return_value = fake_model
        fake_model.invoke.side_effect = [
            AIMessage(content="Secret stored for Thread 1"),
            AIMessage(content="Greetings Thread 2"),
        ]

        config_thread1 = {
            "configurable": {
                "thread_id": "thread-1",
                "model": "test-model",
                "tools": [],
            }
        }
        config_thread2 = {
            "configurable": {
                "thread_id": "thread-2",
                "model": "test-model",
                "tools": [],
            }
        }

        with patch("agent_cli.node.get_model", return_value=fake_model):
            await graph.ainvoke(
                {"messages": [HumanMessage(content="Top secret info for 1")]},
                config=config_thread1,
            )
            await graph.ainvoke(
                {"messages": [HumanMessage(content="Hello from thread 2")]},
                config=config_thread2,
            )

        second_call_messages = fake_model.invoke.call_args_list[1].args[0]
        history_contents = [getattr(m, "content", "") for m in second_call_messages]

        assert any("Hello from thread 2" in c for c in history_contents)
        assert not any("Top secret info for 1" in c for c in history_contents)
        assert not any("Secret stored for Thread 1" in c for c in history_contents)


@pytest.mark.anyio
async def test_async_sqlite_persistence_with_tool_calls(tmp_path):
    """Yeh test verify karta hai ki tool execution ka state (tool call aur uska output) bhi SQLite checkpoint mein theek se persist aur retrieve hota hai."""
    db_path = tmp_path / "async_tools_persistence.sqlite"
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(tools=[sample_tool], checkpointer=checkpointer)

        tool_call_msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "sample_tool",
                    "args": {"query": "weather query"},
                    "id": "call_123",
                    "type": "tool_call",
                }
            ],
        )
        final_answer = AIMessage(content="The tool output was processed: weather query")

        fake_model = Mock()
        fake_model.bind_tools.return_value = fake_model
        fake_model.invoke.side_effect = [tool_call_msg, final_answer]

        config = {
            "configurable": {
                "thread_id": "tool-thread-1",
                "model": "test-model",
                "tools": [sample_tool],
            }
        }

        with patch("agent_cli.node.get_model", return_value=fake_model):
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content="Run tool test")]},
                config=config,
            )

        messages = result["messages"]
        assert any(
            getattr(m, "type", None) == "tool"
            and "processed: weather query" in getattr(m, "content", "")
            for m in messages
        )
        assert messages[-1].content == "The tool output was processed: weather query"

        # Checkpointer ke state mein check karo
        state_tuple = await graph.aget_state(config)
        assert (
            state_tuple.values["messages"][-1].content
            == "The tool output was processed: weather query"
        )


@pytest.mark.anyio
async def test_async_sqlite_persistence_with_astream_events(tmp_path):
    """Yeh test verify karta hai ki graph.astream_events (jo CLI streaming chat me use hota hai) AsyncSqliteSaver ke sath smoothly execute aur persist hota hai."""
    db_path = tmp_path / "async_stream_persistence.sqlite"
    config = {
        "configurable": {
            "thread_id": "stream-thread-1",
            "model": "test-model",
            "tools": [],
        }
    }

    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(tools=[], checkpointer=checkpointer)

        fake_model = Mock()
        fake_model.bind_tools.return_value = fake_model
        fake_model.invoke.return_value = AIMessage(content="Streamed response")

        with patch("agent_cli.node.get_model", return_value=fake_model):
            events = []
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content="Streaming test input")]},
                config=config,
                version="v2",
            ):
                events.append(event)

        assert len(events) > 0
        state_tuple = await graph.aget_state(config)
        assert state_tuple.values["messages"][-1].content == "Streamed response"


@pytest.mark.anyio
async def test_async_sqlite_get_all_threads(tmp_path):
    """Yeh test verify karta hai ki multiple threads me messages persist hone ke baad get_all_threads un saare threads ko correctly fetch aur sort karta hai."""
    db_path = tmp_path / "threads_list.sqlite"
    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(tools=[], checkpointer=checkpointer)
        fake_model = Mock()
        fake_model.bind_tools.return_value = fake_model
        fake_model.invoke.return_value = AIMessage(content="Response")

        with patch("agent_cli.node.get_model", return_value=fake_model):
            await graph.ainvoke(
                {"messages": [HumanMessage(content="Hello Thread 1")]},
                config={
                    "configurable": {
                        "thread_id": "session-1",
                        "model": "test-m",
                        "tools": [],
                    }
                },
            )
            await graph.ainvoke(
                {"messages": [HumanMessage(content="Hello Thread 2")]},
                config={
                    "configurable": {
                        "thread_id": "session-2",
                        "model": "test-m",
                        "tools": [],
                    }
                },
            )

    threads = get_all_threads(db_path)
    assert threads == ["session-1", "session-2"]
