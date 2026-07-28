import os
from dotenv import load_dotenv
from azure.identity import AzureCliCredential, get_bearer_token_provider
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv()

SEARCH_ENDPOINT = os.environ["SEARCH_ENDPOINT"]
SEARCH_KEY = os.environ["SEARCH_KEY"]
EMBEDDING_DEPLOYMENT = os.environ["EMBEDDING_DEPLOYMENT"]
CHAT_DEPLOYMENT = os.environ.get("CHAT_DEPLOYMENT", "gpt-5-mini")
AOAI_ENDPOINT = "https://hello-foundry-muthu.openai.azure.com/"

token_provider = get_bearer_token_provider(
    AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
)
openai_client = AzureOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
)
search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT, index_name="rag-index",
    credential=AzureKeyCredential(SEARCH_KEY),
)

def retrieve(question, k=3):
    q_vector = openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT, input=[question]
    ).data[0].embedding
    vector_query = VectorizedQuery(vector=q_vector, k_nearest_neighbors=k, fields="contentVector")
    results = search_client.search(vector_queries=[vector_query], select=["content", "source"])
    return list(results)

def answer(question):
    chunks = retrieve(question)

    # Build the context block from retrieved chunks, tagged with their source
    context = "\n\n".join(
        f"[Source: {c['source']}]\n{c['content']}" for c in chunks
    )

    system_prompt = (
        "You are a helpful assistant that answers questions using ONLY the provided context. "
        "Rules:\n"
        "- Answer using only information found in the context below.\n"
        "- Always cite the source filename(s) you used, like [Source: filename].\n"
        "- If the context does not contain the answer, respond exactly: "
        "\"I don't know based on the provided documents.\" Do not make anything up."
    )

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = openai_client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Test questions: in-scope, another in-scope, and OUT-of-scope (abstention test)
    questions = [
        "What is the difference between a process and a thread?",
        "What does @SpringBootApplication do?",
        "Who won the 2022 World Cup?", 
        "who is Muthukumar"  # out of scope — should abstain
    ]
    for q in questions:
        print(f"\n{'='*60}\nQ: {q}\n{'='*60}")
        print(answer(q))