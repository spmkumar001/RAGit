import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import AzureCliCredential, get_bearer_token_provider
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType,
    VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
)

load_dotenv()

SEARCH_ENDPOINT = os.environ["SEARCH_ENDPOINT"]
SEARCH_KEY = os.environ["SEARCH_KEY"]
EMBEDDING_DEPLOYMENT = os.environ["EMBEDDING_DEPLOYMENT"]
AOAI_ENDPOINT = "https://hello-foundry-muthu.openai.azure.com/"
INDEX_NAME = "rag-index"
VECTOR_DIMENSIONS = 3072

# ---------- 1. Chunking ----------
def chunk_text(text, chunk_size=800, overlap=100):
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks

# ---------- 2. Read + chunk all docs ----------
docs_folder = Path("documents")
all_chunks = []
chunk_id = 0
for file_path in list(docs_folder.glob("*.md")) + list(docs_folder.glob("*.txt")):
    text = file_path.read_text(encoding="utf-8")
    for chunk in chunk_text(text):
        all_chunks.append({"id": str(chunk_id), "content": chunk, "source": file_path.name})
        chunk_id += 1
print(f"Prepared {len(all_chunks)} chunks.")

# ---------- 3. Embed all chunks (direct AzureOpenAI endpoint, keyless) ----------
token_provider = get_bearer_token_provider(
    AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
)
openai_client = AzureOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
)

def embed_batch(texts):
    resp = openai_client.embeddings.create(model=EMBEDDING_DEPLOYMENT, input=texts)
    return [item.embedding for item in resp.data]

BATCH = 16
for i in range(0, len(all_chunks), BATCH):
    batch = all_chunks[i:i + BATCH]
    vectors = embed_batch([c["content"] for c in batch])
    for c, v in zip(batch, vectors):
        c["contentVector"] = v
    print(f"  Embedded {min(i + BATCH, len(all_chunks))}/{len(all_chunks)}")

# ---------- 4. Create the search index ----------
index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=AzureKeyCredential(SEARCH_KEY))
fields = [
    SearchField(name="id", type=SearchFieldDataType.String, key=True),
    SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
    SearchField(name="source", type=SearchFieldDataType.String, filterable=True),
    SearchField(
        name="contentVector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=VECTOR_DIMENSIONS,
        vector_search_profile_name="my-vector-profile",
    ),
]
vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="my-hnsw")],
    profiles=[VectorSearchProfile(name="my-vector-profile", algorithm_configuration_name="my-hnsw")],
)
index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
index_client.create_or_update_index(index)
print(f"Index '{INDEX_NAME}' created.")

# ---------- 5. Upload chunks ----------
search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=AzureKeyCredential(SEARCH_KEY))
search_client.upload_documents(documents=all_chunks)
print(f"Uploaded {len(all_chunks)} chunks to the index.")