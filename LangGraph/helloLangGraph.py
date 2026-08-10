from typing import TypedDict , Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,AIMessage,HumanMessage
import config as Base
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

class State(TypedDict):
    messages: Annotated[list,add_messages]

client = ChatOpenAI(
    api_key=Base.API_KEY,
    base_url=Base.BASE_URL,
    model=Base.MODEL
)

def chat(state:State):
    reply = client.invoke(state["messages"])
    return {"messages": [reply]}

builder = StateGraph(State)
builder.add_node("chat",chat)
builder.add_edge(START,"chat")
builder.add_edge("chat",END)
graph = builder.compile(checkpointer=checkpointer)
cfg = {"configurable": {"thread_id": "conversation-1"}}

message = [SystemMessage(content="You are a Huge Messi fan and a Ronaldo Hater")]
message.append(HumanMessage(content="Is Messi the Goat? Explain"))
graph.invoke({"messages": [HumanMessage(content="My name is SP")]}, cfg)
r = graph.invoke({"messages": [HumanMessage(content="What is my name?")]}, cfg)
print(r["messages"][-1].content)

print(result["messages"][-1].content)