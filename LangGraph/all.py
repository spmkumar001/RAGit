import config as Base
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,HumanMessage,AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

class State(TypedDict):
    messages : Annotated[list,add_messages]

def getweather(city: str) -> str:
    """ finds the current weather of a given city """
    print("get_weather ran")
    return f"Currently its too sunny in {city}"

tools = [getweather]

llm = ChatOpenAI(
    model=Base.MODEL,
    api_key=Base.API_KEY,
    base_url=Base.BASE_URL
).bind_tools(tools)

def chat(state : State):
    reply = llm.invoke(state["messages"])
    return {"messages":[reply]}

builder = StateGraph(State)
builder.add_node("chat",chat)
builder.add_node("tools",ToolNode(tools))
builder.add_edge(START,"chat")
builder.add_conditional_edges("chat",tools_condition)
builder.add_edge("tools","chat")
graph = builder.compile(checkpointer=checkpointer)


queries = [
    "what is the weather in chennai",
    "who is the GOAT of Football? Just give Name",
    "who is his rival?",
    "which contry and city did we talk about?"
]
cfg = {"configurable" : {"thread_id":"con-1"}}

for q in queries:
    print(q)
    mes = {"messages":[HumanMessage(content=q)]}
    res = graph.invoke(mes,cfg)
    print(res["messages"][-1].content)
    print()

