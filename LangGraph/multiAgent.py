import config as Base
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,HumanMessage,AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field


class Research(BaseModel):
    topic: str = Field(description="the subject researched")
    facts: list[str] = Field(description="key facts about the topic")

class State(TypedDict):
    topic: str
    research_output: Research
    writer_output: str

llm = ChatOpenAI(
    model=Base.MODEL,
    api_key=Base.API_KEY,
    base_url=Base.BASE_URL
)

research_llm = llm.with_structured_output(Research)

def researcher(state:State):
    research = research_llm.invoke(f"List 5 facts about: {state["topic"]}")
    return {"research_output": research}

def writer(state:State):
    write = llm.invoke(f"Write a short paragraph using these facts: {state["research_output"].facts}")
    return {"writer_output": write.content}

builder = StateGraph(State)
builder.add_node("researcher",researcher)
builder.add_node("writer",writer)
builder.add_edge(START,"researcher")
builder.add_edge("researcher","writer")
builder.add_edge("writer",END)
graph = builder.compile()

result = graph.invoke({"topic":"Messi"})
print(f"Research Output : \n{result["research_output"].facts}")
print()
print(f"Writer Output : \n{result["writer_output"]}")
