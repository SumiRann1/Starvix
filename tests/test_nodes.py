from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent_cli.node import chat_node, make_chat_node
from agent_cli.state import SYSTEM_PROMPT

"""This file tests the model selection and the default model fallback"""


def test_chat_node_uses_model_selected_for_run():
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.return_value = AIMessage(content="Hello!")

    state = {"messages": [HumanMessage(content="Hi")]}

    config = {"configurable": {"model": "test-model"}}

    with patch("agent_cli.node.get_model", return_value=fake_model) as mock_get_model:
        result = chat_node(state, config)

    mock_get_model.assert_called_once_with("test-model")
    fake_model.invoke.assert_called_once()

    sent_messages = fake_model.invoke.call_args.args[0]
    assert isinstance(sent_messages[0], SystemMessage)
    assert sent_messages[-1].content == "Hi"
    assert result["messages"][0].content == "Hello!"


def test_chat_node_falls_back_to_default_model():
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.return_value = AIMessage(content="Hello!")

    with patch("agent_cli.node.settings") as mock_settings:
        mock_settings.current_model = "default-test-model"

        with patch(
            "agent_cli.node.get_model", return_value=fake_model
        ) as mock_get_model:
            chat_node({"messages": [HumanMessage(content="Hi")]}, {"configurable": {}})

    mock_get_model.assert_called_once_with("default-test-model")


def test_chat_node_replaces_existing_system_message():
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.return_value = AIMessage(content="Hello!")

    state = {
        "messages": [
            SystemMessage(content="OUTDATED PROMPT"),
            HumanMessage(content="Hi"),
        ],
    }

    with patch("agent_cli.node.get_model", return_value=fake_model):
        chat_node(state, {"configurable": {"model": "test-model"}})

    sent_messages = fake_model.invoke.call_args.args[0]

    assert isinstance(sent_messages[0], SystemMessage)
    assert sent_messages[0].content == SYSTEM_PROMPT
    assert sum(isinstance(message, SystemMessage) for message in sent_messages) == 1


def test_chat_node_does_not_mutate_input_history():
    original_messages = [
        HumanMessage(content="Hi"),
    ]
    state = {"messages": list(original_messages)}

    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.return_value = AIMessage(content="Hello!")

    assert state["messages"] == original_messages


def test_chat_node_with_none_config():
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.return_value = AIMessage(content="Response")

    state = {"messages": [HumanMessage(content="Hi")]}
    with patch("agent_cli.node.get_model", return_value=fake_model):
        result = chat_node(state, None)

    assert result["messages"][0].content == "Response"


def test_chat_node_model_without_bind_tools():
    class SimpleModel:
        def invoke(self, messages):
            return AIMessage(content="Simple response")

    state = {"messages": [HumanMessage(content="Hi")]}
    config = {"configurable": {"model": "test-model", "tools": ["dummy"]}}

    with patch("agent_cli.node.get_model", return_value=SimpleModel()):
        result = chat_node(state, config)

    assert result["messages"][0].content == "Simple response"


def test_make_chat_node_binds_tools():
    fake_model = Mock()
    fake_model.bind_tools.return_value = fake_model
    fake_model.invoke.return_value = AIMessage(content="Response with tools")

    node = make_chat_node(tools=["tool1", "tool2"])
    state = {"messages": [HumanMessage(content="Hi")]}

    with patch("agent_cli.node.get_model", return_value=fake_model):
        result = node(state, None)

    fake_model.bind_tools.assert_called_once_with(["tool1", "tool2"])
    assert result["messages"][0].content == "Response with tools"
