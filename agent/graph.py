from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_google_genai import GoogleGenerativeAI
from langfuse.langchain import CallbackHandler
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    messages: list[Annotated[list, add_messages]]

graph_builder = StateGraph(State)

llm = GoogleGenerativeAI(model="gemini-3.1-flash-lite-preview")

def chatbot(state: State) -> State:
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

graph_builder.set_entry_point("chatbot")

graph_builder.set_finish_point("chatbot")

graph = graph_builder.compile()

langfuse_handler = CallbackHandler()
for s in graph.stream({"messages": [HumanMessage(content = "What is Langfuse?")]},
                      config={"callbacks": [langfuse_handler]}):
    print(s)