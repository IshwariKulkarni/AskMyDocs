# AskMyDocs

A RAG (Retrieval-Augmented Generation) powered document Q&A app. Upload any PDF and ask questions about it in plain English — the AI answers using only the content from your document.

Built with FastAPI, LangChain, ChromaDB, Ollama, and React.js.

This PDF question-answering system was later used as a testbed to benchmark 3 small open-weight models under identical conditions. Full write-up: [EXPERIMENT_REPORT.md](backend/EXPERIMENT_REPORT.md)

---

## What it does

- Upload a PDF through a simple web interface
- The document is split into chunks and stored as vector embeddings in ChromaDB
- Ask any question about the document in a chat UI
- LangChain retrieves the most relevant chunks and passes them to a local LLM (via Ollama) to generate an answer
- Everything runs locally — no OpenAI API key, no cost, no data leaving your machine

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Vite, Axios |
| Backend | Python, FastAPI |
| RAG pipeline | LangChain, LangChain-Community |
| Vector database | ChromaDB |
| Embeddings | Ollama (nomic-embed-text) |
| LLM | Ollama (qwen3:0.6b / llama3) |

---

## Architecture

PDF Upload

↓

PyPDFLoader → RecursiveCharacterTextSplitter → OllamaEmbeddings → ChromaDB

↓

User Question → Embed question → Similarity Search → Top 3 chunks → LLM → Answer

---

## How to run locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) installed and running

### 1. Pull Ollama models

```bash
ollama pull nomic-embed-text
ollama pull qwen3:0.6b
```

### 2. Start the backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`

### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

### 4. Use the app

1. Open `http://localhost:5173` in your browser
2. Upload any PDF using the upload button
3. Wait for the "Indexed X chunks" confirmation
4. Type a question and press Ask

---

## Project structure
askmydocs/

├── backend/

│   ├── main.py              # FastAPI server, RAG pipeline

│   ├── requirements.txt     # Python dependencies

│   └── uploads/             # Uploaded PDFs stored here

└── frontend/

├── src/

│   ├── App.jsx          # Main React component, chat UI

│   └── main.jsx         # Entry point

└── package.json

---

## Key concepts demonstrated

- **RAG pipeline** — retrieval-augmented generation using LangChain
- **Vector embeddings** — converting text chunks into searchable vectors
- **Semantic search** — ChromaDB similarity search to find relevant context
- **Local LLM inference** — running AI models on-device using Ollama
- **REST API design** — FastAPI endpoints with CORS for frontend integration
- **Full-stack integration** — React frontend consuming a Python backend

---

## Screenshots

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/ace8e84d-04f8-4f35-9c2c-97669405f3af" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/fdec328f-8bc5-4993-9e1d-cffa2bad0504" />



## Future improvements

- [ ] Show which page/section of the PDF the answer came from
- [ ] Support multiple PDFs uploaded simultaneously
- [ ] Add streaming responses so answers appear word by word
- [ ] Deploy backend to Railway and frontend to Vercel
- [ ] Swap Ollama for OpenAI API with an env variable toggle

---

## Author

Ishwari Kulkarni — [LinkedIn](https://www.linkedin.com/in/ishwari-kulkarni-2a87b9207/)
