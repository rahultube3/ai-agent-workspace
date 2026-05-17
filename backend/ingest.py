"""
Enhanced ingestion: splits MD by ## and ### headings, adds overlap,
stores rich metadata. Run: python3 backend/ingest.py
"""

import re
from pathlib import Path
import chromadb

ROOT = Path(__file__).parent.parent
MD_FILE = ROOT / "data" / "payment-system.md"
DB_PATH = str(ROOT / "data" / "chroma_db")
COLLECTION = "payment_docs"
OVERLAP_LINES = 3   # lines repeated from previous chunk for context continuity


def chunk_markdown(text: str) -> list[dict]:
    """
    Split at ## (section) and ### (sub-section) headings.
    Attach parent section name to every sub-section chunk.
    Add OVERLAP_LINES from the previous chunk as a prefix.
    """
    # Split on ## or ### headings
    pattern = re.compile(r"(?=^#{2,3} )", re.MULTILINE)
    raw = [c.strip() for c in pattern.split(text) if c.strip()]

    chunks = []
    prev_lines: list[str] = []
    current_section = ""

    for raw_chunk in raw:
        lines = raw_chunk.splitlines()
        heading = lines[0].lstrip("#").strip()
        level = 2 if raw_chunk.startswith("## ") else 3

        if level == 2:
            current_section = heading

        # Build overlap prefix from end of previous chunk
        overlap = "\n".join(prev_lines[-OVERLAP_LINES:]) if prev_lines else ""
        content = (f"[context: {overlap}]\n\n" + raw_chunk) if overlap else raw_chunk

        chunks.append({
            "title": heading,
            "section": current_section,
            "level": level,
            "content": content,
            "word_count": len(raw_chunk.split()),
        })

        prev_lines = lines   # save for next iteration's overlap

    return chunks


def main():
    with open(MD_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_markdown(text)
    print(f"Split into {len(chunks)} chunks\n")

    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION)
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        documents=[c["content"] for c in chunks],
        metadatas=[{
            "title":      c["title"],
            "section":    c["section"],
            "level":      c["level"],
            "word_count": c["word_count"],
        } for c in chunks],
    )

    print(f"{'#':<3} {'Level':<7} {'Section':<35} {'Title':<35} {'Words'}")
    print("-" * 90)
    for i, c in enumerate(chunks):
        lvl = f"H{c['level']}"
        print(f"{i:<3} {lvl:<7} {c['section'][:33]:<35} {c['title'][:33]:<35} {c['word_count']}")

    print(f"\nStored {len(chunks)} chunks → {DB_PATH}")


if __name__ == "__main__":
    main()
