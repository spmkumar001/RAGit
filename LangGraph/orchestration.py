import config as Base
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,HumanMessage,AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated,Literal
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    agent: Literal["math", "writer"] = Field(description="which specialist should handle this request")

class State(TypedDict):
    request: str
    agent_to_use: Literal["math","writer"]
    output: str
    step_count : int
    allowed: bool

llm = ChatOpenAI(
    model=Base.MODEL,
    api_key=Base.API_KEY,
    base_url=Base.BASE_URL
)

router_llm = llm.with_structured_output(RouteDecision)

def supervisor(state:State):
    descision = router_llm.invoke(f"Route this request. {state["request"]}")
    return {"agent_to_use": descision.agent,"step_count": state.get("step_count",0)+1}

def writer(state:State):
    print("Writer Ran")
    result = llm.invoke(state["request"])
    return {"output":result.content}

def math(state:State):
    print("Math Ran")
    result = llm.invoke(state["request"])
    return {"output":result.content}

def route(state: State):
    if state.get("step_count",0) >= 5:
        return END
    return state["agent_to_use"]    

def isallowed(state: State):
    if state.get("allowed") == False:
        # print(f"{state["request"]} is not allowed")
        # state["output": f"{state["request"]} is not allowed"]
        return END
    return "start"

def guardrail(state:State):
    if "Ronaldo" in state["request"]:
        return {"allowed" : False , "output" : f"Blocked: '{state['request']}' is not allowed"}
    return {"allowed" : True}

builder = StateGraph(State)
builder.add_node("supervisor", supervisor)
builder.add_node("math", math)
builder.add_node("writer", writer)
builder.add_node("guardrail", guardrail)

builder.add_edge(START, "guardrail")
builder.add_conditional_edges("guardrail",isallowed,{"start":"supervisor" , END:END})
builder.add_conditional_edges("supervisor",route,{"math":"math","writer":"writer",END:END})
builder.add_edge("math", END)
builder.add_edge("writer", END)
graph = builder.compile()


result = graph.invoke({"request":"What is 150 + 290"})
print(result["output"])

result = graph.invoke({"request":"Who is Messi"})
print(result["output"])


result = graph.invoke({"request":"Who is Ronaldo"})
print(result["output"])