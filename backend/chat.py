"""
RAG chat agent using ChromaDB for retrieval and Groq LLM for generation.
Run: python3 backend/chat.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from groq import Groq

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

COLLECTION = "payment_docs"
DB_PATH = str(ROOT / "data" / "chroma_db")
TOP_K = 3
MODEL = "llama-3.3-70b-versatile"


def retrieve(collection, query: str) -> str:
    results = collection.query(query_texts=[query], n_results=TOP_K)
    parts = []
    for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
        parts.append(f"### {meta['title']}\n{doc}")
    return "\n\n---\n\n".join(parts)


def chat(collection, client: Groq):
    history = []
    system = (
        "You are a helpful assistant that answers questions about a Payment System. "
        "Use only the provided context from the payment system documentation to answer. "
        "If the answer is not in the context, say so clearly."
    )

    print("=" * 50)
    print("  Payment System RAG Agent (powered by Groq)")
    print("=" * 50)
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        context = retrieve(collection, user_input)
        augmented = f"Context from payment system docs:\n\n{context}\n\nQuestion: {user_input}"

        history.append({"role": "user", "content": augmented})

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}] + history,
            max_tokens=1024,
            temperature=0.2,
        )

        answer = response.choices[0].message.content

        # Store clean version in history
        history[-1] = {"role": "user", "content": user_input}
        history.append({"role": "assistant", "content": answer})

        print(f"\nAssistant: {answer}\n")


def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not found. Check your .env file.")

    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    collection = chroma_client.get_collection(COLLECTION)

    groq_client = Groq(api_key=api_key)
    chat(collection, groq_client)


if __name__ == "__main__":
    main()
