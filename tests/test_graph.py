import asyncio
from unittest.mock import Mock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.errors import NodeCancelledError
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agent_cli.graph import build_graph, custom_error_handler
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
        isinstance(message, HumanMessage) and message.content == "A new conversation"
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


def test_build_graph_default_tools():
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    tool_call_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "list_files",
                "args": {"directory": "."},
                "id": "call_default_1",
                "type": "tool_call",
            }
        ],
    )
    final_response = AIMessage(content="Listing finished")
    fake_model.invoke.side_effect = [tool_call_msg, final_response]

    # No tools passed -> defaults to dev_tools + memory_tools
    graph = build_graph()
    assert graph is not None

    with patch("agent_cli.node.get_model", return_value=fake_model):
        result = graph.invoke(
            {"messages": [HumanMessage(content="Show my files")]},
            config={"configurable": {"thread_id": "test-default-tools-thread"}},
        )

    # Verify default tool was routed and executed by the graph
    tool_messages = [
        m for m in result["messages"] if getattr(m, "type", None) == "tool"
    ]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "list_files"
    assert result["messages"][-1].content == "Listing finished"


def test_build_graph_handles_tool_execution_error():
    @tool
    def failing_tool(query: str) -> str:
        """A tool that simulates failure during execution."""
        raise ValueError("simulated tool failure")

    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.side_effect = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "failing_tool",
                    "args": {"query": "fail"},
                    "id": "call_fail_graph",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(content="Apologies, the tool failed."),
    ]
    app_graph = build_graph(tools=[failing_tool])
    config = {
        "configurable": {
            "thread_id": "test-error-thread",
            "model": "test-model",
            "tools": [failing_tool],
        }
    }
    with patch("agent_cli.node.get_model", return_value=fake_model):
        result = app_graph.invoke(
            {"messages": [HumanMessage(content="Run failing tool")]},
            config=config,
        )

    tool_messages = [
        m for m in result["messages"] if getattr(m, "type", None) == "tool"
    ]
    assert len(tool_messages) == 1
    assert "Tool Execution Failed [ValueError]" in tool_messages[0].content
    assert "simulated tool failure" in tool_messages[0].content
    assert "Input argument mismatch" in tool_messages[0].content
    assert result["messages"][-1].content == "Apologies, the tool failed."


def test_tool_node_handles_execution_error_with_handle_tool_errors():
    @tool
    def failing_tool(query: str) -> str:
        """A tool that simulates failure during execution."""
        raise ValueError("simulated tool failure")

    tool_node = ToolNode([failing_tool], handle_tool_errors=True)
    builder = StateGraph(MessagesState)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "tools")
    graph = builder.compile()

    # 1. Graph execution exception ke bina complete ho
    result = graph.invoke(
        {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "failing_tool",
                            "args": {"query": "fail"},
                            "id": "call_fail_handled",
                            "type": "tool_call",
                        }
                    ],
                )
            ]
        }
    )

    # 2. Messages mein failing_tool ke liye ek ToolMessage aaye
    tool_messages = [
        m
        for m in result["messages"]
        if isinstance(m, ToolMessage) or getattr(m, "type", None) == "tool"
    ]
    assert len(tool_messages) == 1
    tool_msg = tool_messages[0]
    assert tool_msg.tool_call_id == "call_fail_handled"
    assert tool_msg.name == "failing_tool"

    # 3. Uske content mein simulated tool failure ho
    assert "simulated tool failure" in str(tool_msg.content)


def test_custom_error_handler_re_raises_interrupts():
    with pytest.raises(KeyboardInterrupt):
        custom_error_handler(KeyboardInterrupt())

    with pytest.raises(SystemExit):
        custom_error_handler(SystemExit(1))


def test_custom_error_handler_guidance_and_truncation():
    # FileNotFoundError guidance
    msg = custom_error_handler(FileNotFoundError("configs/missing.json"))
    assert "Tool Execution Failed [FileNotFoundError]" in msg
    assert "The specified file/path was not found" in msg

    # PermissionError guidance
    msg_perm = custom_error_handler(PermissionError("Access denied"))
    assert "Permission denied for this resource" in msg_perm

    # TimeoutError guidance
    msg_timeout = custom_error_handler(TimeoutError("Operation timed out"))
    assert "The operation timed out" in msg_timeout

    # Truncation for long messages (> 600 chars)
    long_error = ValueError("X" * 1000)
    msg_long = custom_error_handler(long_error)
    assert "... [truncated]" in msg_long


def test_build_graph_propagates_unexpected_programmer_exceptions():
    @tool
    def buggy_attr_tool(query: str) -> str:
        """A tool that raises an unexpected AttributeError (programmer bug)."""
        raise AttributeError("unexpected NoneType attribute access")

    @tool
    def buggy_runtime_tool(query: str) -> str:
        """A tool that raises an unexpected RuntimeError."""
        raise RuntimeError("fatal runtime internal error")

    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model

    # Verify AttributeError is propagated out of the graph and NOT converted to ToolMessage
    fake_model.invoke.return_value = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "buggy_attr_tool",
                "args": {"query": "test"},
                "id": "call_attr",
                "type": "tool_call",
            }
        ],
    )
    graph_attr = build_graph(tools=[buggy_attr_tool])
    with (
        patch("agent_cli.node.get_model", return_value=fake_model),
        pytest.raises(AttributeError, match="unexpected NoneType attribute access"),
    ):
        graph_attr.invoke(
            {"messages": [HumanMessage(content="run attr")]},
            config={
                "configurable": {
                    "thread_id": "test-attr",
                    "model": "m",
                    "tools": [buggy_attr_tool],
                }
            },
        )

    # Verify RuntimeError is propagated out of the graph and NOT converted to ToolMessage
    fake_model.invoke.return_value = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "buggy_runtime_tool",
                "args": {"query": "test"},
                "id": "call_rt",
                "type": "tool_call",
            }
        ],
    )
    graph_rt = build_graph(tools=[buggy_runtime_tool])
    with (
        patch("agent_cli.node.get_model", return_value=fake_model),
        pytest.raises(RuntimeError, match="fatal runtime internal error"),
    ):
        graph_rt.invoke(
            {"messages": [HumanMessage(content="run rt")]},
            config={
                "configurable": {
                    "thread_id": "test-rt",
                    "model": "m",
                    "tools": [buggy_runtime_tool],
                }
            },
        )


def test_build_graph_propagates_interrupts_and_cancellation():
    @tool
    def kbi_tool(query: str) -> str:
        """A tool simulating Ctrl+C interrupt."""
        raise KeyboardInterrupt()

    @tool
    def exit_tool(query: str) -> str:
        """A tool simulating SystemExit."""
        raise SystemExit(1)

    @tool
    def cancel_tool(query: str) -> str:
        """A tool simulating cancellation."""
        raise asyncio.CancelledError("async task cancelled")

    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model

    # 1. KeyboardInterrupt must propagate directly
    fake_model.invoke.return_value = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "kbi_tool",
                "args": {"query": "test"},
                "id": "call_kbi",
                "type": "tool_call",
            }
        ],
    )
    graph_kbi = build_graph(tools=[kbi_tool])
    with (
        patch("agent_cli.node.get_model", return_value=fake_model),
        pytest.raises(KeyboardInterrupt),
    ):
        graph_kbi.invoke(
            {"messages": [HumanMessage(content="run kbi")]},
            config={
                "configurable": {
                    "thread_id": "test-kbi",
                    "model": "m",
                    "tools": [kbi_tool],
                }
            },
        )

    # 2. SystemExit must propagate directly
    fake_model.invoke.return_value = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "exit_tool",
                "args": {"query": "test"},
                "id": "call_exit",
                "type": "tool_call",
            }
        ],
    )
    graph_exit = build_graph(tools=[exit_tool])
    with (
        patch("agent_cli.node.get_model", return_value=fake_model),
        pytest.raises(SystemExit),
    ):
        graph_exit.invoke(
            {"messages": [HumanMessage(content="run exit")]},
            config={
                "configurable": {
                    "thread_id": "test-exit",
                    "model": "m",
                    "tools": [exit_tool],
                }
            },
        )

    # 3. asyncio.CancelledError must propagate (as NodeCancelledError or CancelledError)
    fake_model.invoke.return_value = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "cancel_tool",
                "args": {"query": "test"},
                "id": "call_cancel",
                "type": "tool_call",
            }
        ],
    )
    graph_cancel = build_graph(tools=[cancel_tool])
    with (
        patch("agent_cli.node.get_model", return_value=fake_model),
        pytest.raises((asyncio.CancelledError, NodeCancelledError)),
    ):
        graph_cancel.invoke(
            {"messages": [HumanMessage(content="run cancel")]},
            config={
                "configurable": {
                    "thread_id": "test-cancel",
                    "model": "m",
                    "tools": [cancel_tool],
                }
            },
        )
