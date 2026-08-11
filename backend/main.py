from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
import shutil, os

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

    llm = OllamaLLM(model="phi3", temperature=0)
    answer = llm.invoke(prompt)
    return {"answer": answer}