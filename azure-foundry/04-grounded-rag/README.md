# Project 4 — Grounded Agent (RAG)

## What it does
A retrieval-augmented generation pipeline over 5 personal markdown documents
(Java, Spring, Python, RAG, football). Chunks documents, embeds them with
text-embedding-3-large, stores vectors in Azure AI Search, then answers questions
grounded in retrieved chunks — with source citations, and abstention when the
documents don't support an answer.

## Pipeline (built and tested in stages)
1. **Load** — read .md files (plain text, clean; skipped messy PDF extraction).
2. **Chunk** — 800-char chunks with 100-char overlap (122 chunks total).
3. **Embed** — text-embedding-3-large → 3072-dim vectors, batched (16 at a time).
4. **Store** — Azure AI Search index (Free tier) with an HNSW vector profile.
5. **Retrieve** — embed the question, vector-search top-k nearest chunks.
6. **Generate** — feed retrieved chunks to gpt-5-mini with a system prompt that
   enforces grounding, citation, and abstention.

## Key concepts learned
- **Retrieval quality dominates model quality** — verified: correct doc retrieved
  for each question, scores ranked meaningfully.
- **Citation** comes from storing the source filename with each chunk and
  instructing the model to cite it.
- **Abstention** happens at the *generation* step, not retrieval — retrieval always
  returns k chunks; the model decides they don't answer the question and refuses.
  Proven: "who is Muthukumar" → "I don't know based on the provided documents."
- **HNSW** is configured on the index (field → profile → algorithm), used
  automatically on every vector search. At 122 chunks it's overkill; it matters at
  scale, where it trades a sliver of accuracy for large speed gains.
- **Index is persistent cloud state** — defined once by build_index.py, then any
  client (any query script) uses it. Python files are ephemeral clients; the index,
  vectors, and profile live in Azure.

## What broke and how I diagnosed it
The **embedding call 404'd** through the project endpoint (services.ai.azure.com)
even though chat worked fine on the same endpoint. Root cause: the project endpoint
misroutes embedding calls. Fix: call embeddings through the **direct Azure OpenAI
endpoint** (.openai.azure.com) using the AzureOpenAI client with a keyless bearer
token provider. Isolated the bug with a one-input test script before touching the
full indexer.

## Cost
Free-tier Azure AI Search ($0). Embedding 122 chunks + queries = pennies on
text-embedding-3-large / gpt-5-mini. Note: Free-tier search may be deleted after
long inactivity (would require re-running build_index.py).

## What I'd do differently at scale
- Smarter chunking (cut on markdown headers / sentences, not blind char count) and
  measure retrieval precision before/after.
- Hybrid search (vector + keyword) for better recall.
- Keep the search service in the same region as the models (mine landed in Central US
  vs East US models — works, but cross-region adds latency).