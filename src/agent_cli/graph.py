from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from .node import chat_node
from .state import AgentState

def build_graph(state=AgentState):

    graph_builder = StateGraph(state)

    graph_builder.add_node("chat", chat_node)
    graph_builder.add_edge(START, "chat")
    graph_builder.add_edge("chat", END)

    return graph_builder.compile(checkpointer=MemorySaver())

#Running the graph
# if __name__ == "__main__":
#     graph = build_graph()
#     print(graph.invoke({"query": "Hello"}))