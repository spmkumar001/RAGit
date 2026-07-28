from pathlib import Path

docs_folder = Path("documents")

# Read all .md and .txt files
for file_path in list(docs_folder.glob("*.md")) + list(docs_folder.glob("*.txt")):
    text = file_path.read_text(encoding="utf-8")
    print(f"\n{'='*60}")
    print(f"FILE: {file_path.name}")
    print(f"Characters: {len(text)}")
    print(f"--- First 300 characters ---")
    print(text[:300])