"""
Enhanced FastAPI RAG backend.
Features: streaming SSE, query rewriting, similarity scores, /search debug.
Run: python3 -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import chromadb
from groq import Groq

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

COLLECTION  = "payment_docs"
DB_PATH     = str(ROOT / "data" / "chroma_db")
TOP_K       = 4
MODEL       = "llama-3.3-70b-versatile"
SYSTEM      = (
    "You are a helpful expert assistant for a Payment System. "
    "Answer ONLY from the provided context. Be concise and accurate. "
    "Use bullet points or tables when helpful. "
    "If the answer is not in the context, clearly say so."
)

# --- Init ---
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError("GROQ_API_KEY not found in .env")

groq_client   = Groq(api_key=api_key)
chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection    = chroma_client.get_collection(COLLECTION)

# --- App ---
app = FastAPI(title="Payment RAG API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(ROOT / "frontend")), name="static")


# --- Schemas ---
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class Source(BaseModel):
    title: str
    section: str
    snippet: str
    score: float          # similarity 0–1 (higher = more relevant)


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    rewritten_query: str


# --- Helpers ---
def rewrite_query(question: str) -> str:
    """Ask Groq to produce a better retrieval query from the user's question."""
    resp = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "system",
            "content": (
                "You are a query optimizer for a payment system knowledge base. "
                "Rewrite the user's question into a short, keyword-rich search query "
                "that will retrieve the most relevant documents. "
                "Return ONLY the rewritten query, nothing else."
            ),
        }, {
            "role": "user",
            "content": question,
        }],
        max_tokens=60,
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


def retrieve(query: str) -> tuple[str, list[Source]]:
    """Query ChromaDB and return formatted context + source objects."""
    results = collection.query(
        query_texts=[query],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    sources = []
    context_parts = []

    for meta, doc, dist in zip(
        results["metadatas"][0],
        results["documents"][0],
        results["distances"][0],
    ):
        # ChromaDB cosine distance → similarity
        similarity = round(1 - dist, 3)
        sources.append(Source(
            title=meta.get("title", ""),
            section=meta.get("section", ""),
            snippet=doc[:250],
            score=similarity,
        ))
        context_parts.append(
            f"### {meta.get('section', '')} › {meta.get('title', '')}\n{doc}"
        )

    return "\n\n---\n\n".join(context_parts), sources


def build_messages(context: str, question: str, history: list[dict]) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM}]
    messages += history[-10:]   # keep last 5 turns
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {question}",
    })
    return messages


# --- Routes ---
@app.get("/")
def serve_ui():
    return FileResponse(str(ROOT / "frontend" / "index.html"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL,
        "chunks": collection.count(),
        "top_k": TOP_K,
    }


@app.get("/search")
def search(q: str, n: int = 4):
    """Debug endpoint — returns raw retrieval results for a query."""
    if not q:
        raise HTTPException(400, "Provide ?q=your+query")
    _, sources = retrieve(q)
    return {"query": q, "results": [s.model_dump() for s in sources]}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty.")

    rewritten = rewrite_query(req.message)
    context, sources = retrieve(rewritten)
    messages = build_messages(context, req.message, req.history)

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=1024,
        temperature=0.2,
    )
    answer = response.choices[0].message.content
    return ChatResponse(answer=answer, sources=sources, rewritten_query=rewritten)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Server-Sent Events streaming endpoint."""
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty.")

    rewritten = rewrite_query(req.message)
    context, sources = retrieve(rewritten)
    messages = build_messages(context, req.message, req.history)

    def generate():
        # First emit sources metadata
        yield f"data: {json.dumps({'type': 'sources', 'sources': [s.model_dump() for s in sources], 'rewritten_query': rewritten})}\n\n"

        # Stream answer tokens
        stream = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.2,
            stream=True,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT)],
    )
