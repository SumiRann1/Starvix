from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from agent_cli.graph import build_graph
from agent_cli.state import SYSTEM_PROMPT


def test_graph_invokes_chat_node_and_returns_response():
    fake_model = Mock()
    fake_model.invoke.return_value = AIMessage(content="Mock response")

    graph = build_graph()

    config = {"configurable": {"thread_id": "test-thread", "model": "test-model"}}

    with patch("agent_cli.node.get_model", return_value=fake_model):
        result = graph.invoke(
            {"messages": [HumanMessage(content="Hello")]},
            config=config,
        )

    assert result["messages"][-1].content == "Mock response"

    sent_messages = fake_model.invoke.call_args.args[0]
    assert isinstance(sent_messages[0], SystemMessage)
    assert sent_messages[0].content == SYSTEM_PROMPT
