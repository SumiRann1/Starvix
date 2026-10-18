from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool

from agent_cli.graph import build_graph
from agent_cli.state import SYSTEM_PROMPT


@tool
def dummy_tool(query: str) -> str:
    """A test tool."""
    return query


@pytest.fixture
def tools():
    return [dummy_tool]


def test_graph_invokes_chat_node_and_returns_response(tools):
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.return_value = AIMessage(content="Mock response")

    graph = build_graph(tools=tools)

    config = {
        "configurable": {
            "thread_id": "test-thread",
            "model": "test-model",
            "tools": tools,
        }
    }

    with patch("agent_cli.node.get_model", return_value=fake_model):
        result = graph.invoke(
            {"messages": [HumanMessage(content="Hello")]},
            config=config,
        )

    assert result["messages"][-1].content == "Mock response"

    sent_messages = fake_model.invoke.call_args.args[0]
    assert isinstance(sent_messages[0], SystemMessage)
    assert sent_messages[0].content == SYSTEM_PROMPT
    fake_model.bind_tools.assert_called_once_with(tools)


def test_same_thread_preserves_conversation_history(tools):
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.side_effect = [
        AIMessage(content="Hello!"),
        AIMessage(content="You said hello earlier."),
    ]

    graph = build_graph(tools=tools)
    config = {
        "configurable": {
            "thread_id": "conversation-a",
            "model": "test-model",
            "tools": tools,
        }
    }

    with patch("agent_cli.node.get_model", return_value=fake_model):
        graph.invoke(
            {"messages": [HumanMessage(content="Hi")]},
            config=config,
        )
        graph.invoke(
            {"messages": [HumanMessage(content="What did I say?")]},
            config=config,
        )

    second_call_messages = fake_model.invoke.call_args_list[1].args[0]

    assert any(
        isinstance(message, HumanMessage) and message.content == "Hi"
        for message in second_call_messages
    )
    assert any(
        isinstance(message, AIMessage) and message.content == "Hello!"
        for message in second_call_messages
    )
    assert second_call_messages[-1].content == "What did I say?"


def test_different_threads_do_not_share_history(tools):
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.side_effect = [
        AIMessage(content="Secret for thread A"),
        AIMessage(content="Response for thread B"),
    ]

    graph = build_graph(tools=tools)

    config_a = {
        "configurable": {
            "thread_id": "conversation-a",
            "model": "test-model",
            "tools": tools,
        }
    }
    config_b = {
        "configurable": {
            "thread_id": "conversation-b",
            "model": "test-model",
            "tools": tools,
        }
    }

    with patch("agent_cli.node.get_model", return_value=fake_model):
        graph.invoke(
            {"messages": [HumanMessage(content="My private topic")]},
            config=config_a,
        )
        graph.invoke(
            {"messages": [HumanMessage(content="A new conversation")]},
            config=config_b,
        )

    second_call_messages = fake_model.invoke.call_args_list[1].args[0]

    assert any(
        isinstance(message, HumanMessage)
        and message.content == "A new conversation"
        for message in second_call_messages
    )
    assert not any(
        getattr(message, "content", None) == "My private topic"
        for message in second_call_messages
    )
    assert not any(
        getattr(message, "content", None) == "Secret for thread A"
        for message in second_call_messages
    )


def test_build_graph_uses_provided_tools(tools):
    with patch("agent_cli.graph.get_tools_sync") as mock_get_tools:
        graph = build_graph(tools=tools)
        mock_get_tools.assert_not_called()
        assert graph is not None


def test_build_graph_falls_back_to_get_tools_sync_when_none(tools):
    with patch("agent_cli.graph.get_tools_sync", return_value=tools) as mock_get_tools:
        graph = build_graph()
        mock_get_tools.assert_called_once()
        assert graph is not None


def test_graph_executes_tool_call_and_returns_response(tools):
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model

    tool_call_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "dummy_tool",
                "args": {"query": "tool argument"},
                "id": "call_123",
                "type": "tool_call",
            }
        ],
    )
    final_response = AIMessage(content="Final response after tool execution")
    fake_model.invoke.side_effect = [tool_call_message, final_response]

    graph = build_graph(tools=tools)

    config = {
        "configurable": {
            "thread_id": "test-tool-thread",
            "model": "test-model",
            "tools": tools,
        }
    }

    with patch("agent_cli.node.get_model", return_value=fake_model):
        result = graph.invoke(
            {"messages": [HumanMessage(content="Run tool")]},
            config=config,
        )

    assert result["messages"][-1].content == "Final response after tool execution"
    assert any(
        getattr(m, "type", None) == "tool" and m.content == "tool argument"
        for m in result["messages"]
    )
