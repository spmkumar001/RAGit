import config as Base
from langchain_openai import ChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader,DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List

# ============================================================
# PART 1 — OFFLINE INDEXING (runs once at startup)
# ============================================================

loader = DirectoryLoader(
    "LangGraph\documents",
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding":"utf-8"}
)

raw_docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=800,chunk_overlap=100)
chunks = splitter.split_documents(raw_docs)

embedding_obj = AzureOpenAIEmbeddings(
    azure_deployment=Base.EMBEDDING_MODEL,
    azure_endpoint=Base.AZURE_ENDPOINT,
    api_key=Base.API_KEY,
    api_version=Base.EMBEDDING_API_VERSION
)

vectorstore = FAISS.from_documents(chunks,embedding_obj)
retriever = vectorstore.as_retriever(search_kwargs={"k":3})

# ============================================================
# PART 2 — THE CHAT MODEL (your FIRST model) — generates the answer
# ============================================================
llm = ChatOpenAI(
    model=Base.MODEL,
    api_key=Base.API_KEY,
    base_url=Base.BASE_URL,
)

# ============================================================
# PART 3 — THE GRAPH: retrieve -> generate
# ============================================================

class State(TypedDict):
    question: str
    context: List[str]     # retrieved chunk texts land here
    answer: str

def retrieve(state: State):
    docs = retriever.invoke(state["question"])            # embed question, find nearest chunks
    return {"context": [d.page_content for d in docs]}

def generate(state: State):
    context = "\n\n".join(state["context"])
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the answer is not in the context, reply exactly: I don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {state['question']}"
    )
    reply = llm.invoke(prompt)
    return {"answer": reply.content}

builder = StateGraph(State)
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)
graph = builder.compile()

# ============================================================
# RUN — test grounding AND abstention
# ============================================================
def ask(q):
    result = graph.invoke({"question": q})
    print(f"\nQ: {q}")
    print(f"A: {result['answer']}")
    print()
    # print("--- context used ---")
    # for c in result["context"]:
    #     print("  -", c)

ask("Where is Growfin based?")
ask("Who is Messi")
ask("Explain the need of Spring Boot")
