from pypdf import PdfReader
from pathlib import Path

docs_folder = Path("documents")

for pdf_path in docs_folder.glob("*.pdf"):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    print(f"\n{'='*60}")
    print(f"FILE: {pdf_path.name}")
    print(f"Pages: {len(reader.pages)}")
    print(f"Total characters: {len(text)}")
    print(f"--- First 500 characters ---")
    print(text[:500])