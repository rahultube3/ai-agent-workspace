# Payment System RAG Chat Agent

A Retrieval-Augmented Generation (RAG) chat agent for the Payment System documentation. Ask questions in natural language and get accurate, context-grounded answers powered by **Groq LLaMA 3.3 70B** and **ChromaDB**.

---

## Features

- **RAG Pipeline** — Retrieves the most relevant document chunks before answering
- **Query Rewriting** — Automatically rephrases questions for better retrieval
- **Streaming Responses** — Answers stream token by token via SSE
- **Similarity Scores** — Each source shows a relevance score (0–100%)
- **Multi-turn Chat** — Remembers conversation history across turns
- **REST API** — FastAPI backend with `/chat`, `/chat/stream`, `/search`, `/health`
- **Chat UI** — Clean browser interface with markdown rendering

---

## Project Structure

```
├── .env                        # API keys (not committed)
├── .gitignore
├── requirements.txt
│
├── backend/
│   ├── ingest.py               # Embed MD file into ChromaDB
│   ├── api.py                  # FastAPI server (REST + streaming)
│   └── chat.py                 # Terminal chat interface
│
├── frontend/
│   └── index.html              # Browser chat UI
│
└── data/
    ├── payment-system.md       # Source knowledge base
    └── chroma_db/              # Vector database (auto-generated)
```

---

## Setup

### 1. Clone & install dependencies

```bash
git clone <repo-url>
cd ai-agent-workspace
pip3 install -r requirements.txt
```

### 2. Configure API key

Create a `.env` file in the root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your free key at: https://console.groq.com/keys

### 3. Ingest the knowledge base

```bash
python3 backend/ingest.py
```

This reads `data/payment-system.md`, splits it into chunks, and stores them in ChromaDB.

### 4. Start the server

```bash
python3 -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

### 5. Open the chat UI

Visit: **http://127.0.0.1:8000**

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve the chat UI |
| `GET` | `/health` | Server status, model, chunk count |
| `POST` | `/chat` | Full response (JSON) |
| `POST` | `/chat/stream` | Streaming response (SSE) |
| `GET` | `/search?q=query` | Raw retrieval debug |

### Example — `/chat`

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How does fraud detection work?"}'
```

Response:
```json
{
  "answer": "Fraud detection uses a risk scoring engine...",
  "sources": [
    { "title": "Risk Scoring Engine", "section": "Fraud Detection", "score": 0.87 }
  ],
  "rewritten_query": "fraud detection methods payment systems"
}
```

### Example — `/search` (debug)

```bash
curl "http://127.0.0.1:8000/search?q=refund+process"
```

---

## Terminal Chat

To use the agent directly in the terminal without the UI:

```bash
python3 backend/chat.py
```

---

## Knowledge Base Topics

The `data/payment-system.md` file covers:

- Core Functionalities (initiation, auth, processing, settlement, refunds)
- Transaction Lifecycle & Statuses
- Supported Payment Methods
- Error Handling
- Compliance & Standards (PCI-DSS, AML, KYC, GDPR)
- Fraud Detection & Risk Management
- Multi-Currency & FX Support
- Subscription & Recurring Payments
- Payment Gateway Integration (webhooks, idempotency, rate limits)
- Payment Analytics & Reporting

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq — LLaMA 3.3 70B |
| Vector DB | ChromaDB (local, persistent) |
| Backend | FastAPI + Uvicorn |
| Frontend | Vanilla HTML / CSS / JS |
| Embeddings | ChromaDB default (all-MiniLM-L6-v2) |

---

## Re-ingesting After MD Changes

Whenever you update `data/payment-system.md`, re-run:

```bash
python3 backend/ingest.py
```

Then restart the server.
