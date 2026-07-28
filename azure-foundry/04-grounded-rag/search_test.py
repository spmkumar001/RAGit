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
AOAI_ENDPOINT = "https://hello-foundry-muthu.openai.azure.com/"

# Embedding client (same working setup as build_index)
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

# --- Ask a question ---
question = "What is the difference between a process and a thread?"

# 1. Embed the question
q_vector = openai_client.embeddings.create(
    model=EMBEDDING_DEPLOYMENT, input=[question]
).data[0].embedding

# 2. Search the index for the most similar chunks
vector_query = VectorizedQuery(vector=q_vector, k_nearest_neighbors=3, fields="contentVector")
results = search_client.search(vector_queries=[vector_query], select=["content", "source"])

# 3. Show what came back
print(f"QUESTION: {question}\n")
for i, r in enumerate(results, 1):
    print(f"--- Result {i} (from {r['source']}, score {r['@search.score']:.3f}) ---")
    print(r["content"][:300])
    print()