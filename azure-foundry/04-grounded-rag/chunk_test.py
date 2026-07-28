from pathlib import Path

docs_folder = Path("documents")

def chunk_text(text, chunk_size=800, overlap=100):
    """Split text into overlapping chunks of ~chunk_size characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # step forward, but back up by `overlap`
    return chunks

total_chunks = 0
for file_path in list(docs_folder.glob("*.md")) + list(docs_folder.glob("*.txt")):
    text = file_path.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    total_chunks += len(chunks)
    print(f"\n{'='*60}")
    print(f"FILE: {file_path.name}  ->  {len(chunks)} chunks")
    print(f"--- First chunk ---")
    print(chunks[0])
    print(f"--- (chunk length: {len(chunks[0])} chars) ---")

print(f"\n{'='*60}")
print(f"TOTAL CHUNKS ACROSS ALL DOCS: {total_chunks}")