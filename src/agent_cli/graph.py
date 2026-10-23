from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.memory import InMemoryStore

from .node import make_chat_node
from .state import AgentState
from .tool.dev_tools import dev_tools
from .tool.memory import memory_tools


def build_graph(state=AgentState, tools=None, checkpointer=None, store=None):
    #Agar tools diye nahi gayenge toh default tools use honge iski wajah se error aa rahi thi
    if tools is None:
        tools = dev_tools+memory_tools
    
    graph_builder = StateGraph(state)

    # Ab chat node banega tools ke saath
    chat_node_instance = make_chat_node(tools)
    graph_builder.add_node("chat", chat_node_instance)
    
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "chat")
    graph_builder.add_conditional_edges("chat", tools_condition)
    graph_builder.add_edge("tools", "chat")

    if checkpointer is None:
        checkpointer=MemorySaver()
    if store is None:
        store = InMemoryStore()

    return graph_builder.compile(checkpointer=checkpointer, store =store)
