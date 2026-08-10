from typing import TypedDict,Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,AIMessage,HumanMessage
import config as Base
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

class State(TypedDict):
    messages : Annotated[list,add_messages]

def get_weather(city: str) -> str:
    """ Get the Current Weather for a given city """
    print("ran weather")
    if city == "Chennai":
        return f"Sunny in {city}"
    elif city == "Bangalore":
        return f"Cold and freezing in {city}"
    else:
        return f"Unknown city {city}"

def multiply(a: int, b: int) -> int:
    """ Multiplies 2 integers """
    print("ran multiply tool")
    return a*b

tools = [get_weather,multiply]

llm = ChatOpenAI(
    model=Base.MODEL,
    api_key=Base.API_KEY,
    base_url=Base.BASE_URL
).bind_tools(tools)

def chat(state:State):
    reply = llm.invoke(state["messages"])
    return {"messages": [reply]}

builder = StateGraph(State)
builder.add_node("chat",chat)
builder.add_node("tools",ToolNode(tools))
builder.add_edge(START,"chat")
builder.add_conditional_edges("chat",tools_condition)
builder.add_edge("tools","chat")
graph = builder.compile(checkpointer=checkpointer)

cfg = {"configurable": {"thread_id": "conversation-1"}}

queries = [
    "My name is SP and I am a Messi fan",
    "What is 457651 * 1276522?",
    "What's the weather in Chennai?",
    "What is my name?",              # tests memory of query 1
    "Which player did I say I like?" # tests memory again
]

for str in queries:
    print(str)
    r =graph.invoke({"messages": [HumanMessage(content=str)]}, cfg)
    print(r["messages"][-1].content)
    print()