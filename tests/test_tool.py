import os
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from agent_cli.graph import build_graph
from agent_cli.tool.tavily_tool import client, get_tools, get_tools_sync


def test_client_configuration():
    assert "tavily" in client.connections
    connection = client.connections["tavily"]
    assert connection["transport"] == "streamable_http"


@pytest.mark.anyio
async def test_get_tools_async():
    @tool
    def dummy_tool(query: str) -> str:
        """A test tool."""
        return query

    with patch(
        "agent_cli.tool.tavily_tool.client.get_tools",
        new=AsyncMock(return_value=[dummy_tool]),
    ):
        tools = await get_tools()
        assert len(tools) == 1
        assert tools[0].name == "dummy_tool"


def test_get_tools_sync_without_running_loop():
    @tool
    def dummy_tool(query: str) -> str:
        """A test tool."""
        return query

    with patch(
        "agent_cli.tool.tavily_tool.client.get_tools",
        new=AsyncMock(return_value=[dummy_tool]),
    ):
        tools = get_tools_sync()
        assert len(tools) == 1
        assert tools[0].name == "dummy_tool"


@pytest.mark.anyio
async def test_get_tools_sync_with_running_loop():
    @tool
    def dummy_tool(query: str) -> str:
        """A test tool."""
        return query

    with patch(
        "agent_cli.tool.tavily_tool.client.get_tools",
        new=AsyncMock(return_value=[dummy_tool]),
    ):
        # Inside an async test, an event loop is running, triggering the ThreadPoolExecutor branch
        tools = get_tools_sync()
        assert len(tools) == 1
        assert tools[0].name == "dummy_tool"


@tool
def get_project_status() -> str:
    """Return the project status. Use this when asked about project status."""
    return "FORGE_STATUS: TOOL_EXECUTED_SUCCESSFULLY"


@pytest.mark.integration
def test_real_model_calls_tool():
    model_id = os.getenv("FORGE_TEST_MODEL")

    if not model_id:
        pytest.skip("Set FORGE_TEST_MODEL to run the real-provider test")

    graph = build_graph(tools=[get_project_status])
    config = {
        "configurable": {
            "thread_id": "real-tool-call-test",
            "model": model_id,
        }
    }

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "You must call the get_project_status tool before answering. "
                        "Tell me the exact status returned by the tool."
                    )
                )
            ]
        },
        config=config,
    )

    messages = result["messages"]

    tool_messages = [
        message for message in messages if isinstance(message, ToolMessage)
    ]

    assert tool_messages, "The model did not execute any tool."
    assert any(
        "TOOL_EXECUTED_SUCCESSFULLY" in str(message.content)
        for message in tool_messages
    ), "The expected tool result was not found."

    assert isinstance(messages[-1], AIMessage)
    assert "TOOL_EXECUTED_SUCCESSFULLY" in str(messages[-1].content)
