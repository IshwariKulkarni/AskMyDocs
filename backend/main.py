from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
import shutil, os
import ollama 
import psutil
import threading
import time

app = FastAPI()

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"])

os.makedirs("uploads", exist_ok=True)
embeddings = OllamaEmbeddings(model="nomic-embed-text")
db = None

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global db
    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    loader = PyPDFLoader(path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    db = Chroma.from_documents(chunks, embeddings)
    return {"message": f"Indexed {len(chunks)} chunks"}

@app.post("/ask")
async def ask_question(body: dict):
    if db is None:
        return {"answer": "Please upload a PDF first."}

    question = body["question"]
    model_name = body.get("model", "phi3")
    relevant_chunks = db.similarity_search(question, k=3)
    context = "\n\n".join([chunk.page_content for chunk in relevant_chunks])

    # DEBUG PRINTS
    print("=" * 40)
    print("USER QUESTION:", question)
    print("RETRIEVED CONTEXT:\n", context)
    print("=" * 40)

    prompt = f"""You are a helpful assistant reading a document. Use the provided context to answer the user's question. 
If the question is a greeting or general query (like "can you help me?"), acknowledge it and invite them to ask specific 
questions about the document content. Use the following context from a document to answer the question.
If the answer is not in the context, say "I couldn't find that in the document."

Context:
{context}

Question: {question}

Answer:"""

     # ---- RAM tracking setup ----
    ram_before_mb = psutil.virtual_memory().used / (1024 * 1024)
    peak_ram_mb = ram_before_mb
    stop_sampling = threading.Event()

    def sample_ram():
        nonlocal peak_ram_mb
        while not stop_sampling.is_set():
            current = psutil.virtual_memory().used / (1024 * 1024)
            if current > peak_ram_mb:
                peak_ram_mb = current
            time.sleep(0.2)  # sample every 200ms

    sampler_thread = threading.Thread(target=sample_ram)
    sampler_thread.start()

    # llm = OllamaLLM(model="phi3", temperature=0)
    # answer = llm.invoke(prompt)
    # return {"answer": answer}

    response = ollama.generate(
        model = model_name,
        prompt = prompt,
        options = {"temperature":0}
    )

     # ---- Stop RAM sampling ----
    stop_sampling.set()
    sampler_thread.join()
    ram_after_mb = psutil.virtual_memory().used / (1024 * 1024)

    total_duration_ms = response.get("total_duration", 0) / 1_000_000
    load_duration_ms = response.get("load_duration", 0) / 1_000_000
    prompt_eval_duration_ms = response.get("prompt_eval_duration", 0) / 1_000_000
    eval_duration_ms = response.get("eval_duration", 0) / 1_000_000
    prompt_tokens = response.get("prompt_eval_count", 0)
    output_tokens = response.get("eval_count", 0)

    tokens_per_second = (
        output_tokens / (eval_duration_ms / 1000)
        if eval_duration_ms > 0 else 0
    )

    is_cold_start = load_duration_ms > 1000

    return {
        "answer": response["response"],
        "model": model_name,
        "metrics": {
            "total_duration_ms": round(total_duration_ms, 2),
            "load_duration_ms": round(load_duration_ms, 2),
            "prompt_eval_duration_ms": round(prompt_eval_duration_ms, 2),
            "generation_duration_ms": round(eval_duration_ms, 2),
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "tokens_per_second": round(tokens_per_second, 2),
            "is_cold_start": is_cold_start
        },
        "resources":{
            "ram_before_mb": round(ram_before_mb, 1),
            "peak_ram_mb": round(peak_ram_mb, 1),
            "ram_after_mb": round(ram_after_mb, 1),
            "ram_delta_mb": round(peak_ram_mb - ram_before_mb, 1)
        }
    }