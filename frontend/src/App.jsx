import { useEffect, useRef, useState } from "react"
import axios from "axios"
import "./App.css"

const API = "http://localhost:8000"

function formatBytes(bytes) {
  if (!bytes) return "0 KB"
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(0)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

function IconLogo() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M14 2v5h5" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M8.5 13.5 10.5 15l3-3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconUpload() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M12 15V4M12 4l-4 4M12 4l4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconPdf() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <path d="M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <path d="M14 2v5h5" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  )
}

function IconClose() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function IconCheck() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
      <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconAlert() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
      <path d="M12 9v4M12 17h.01" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  )
}

function IconChat() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconSend() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
      <path d="M22 2 11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M22 2 15 22l-4-9-9-4 20-7Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

const STEPS = [
  "Upload a PDF — it's split into chunks and embedded into a vector store.",
  "Ask a question in plain English about the document's contents.",
  "The most relevant chunks are retrieved and passed to a local LLM.",
  "Get an answer grounded only in your document — nothing leaves your machine.",
]

export default function App() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState(null)
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [docReady, setDocReady] = useState(false)

  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  function handleFileSelect(f) {
    if (!f) return
    if (f.type !== "application/pdf") {
      setStatus({ type: "error", text: "Only PDF files are supported." })
      return
    }
    setFile(f)
    setStatus(null)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragActive(false)
    handleFileSelect(e.dataTransfer.files?.[0])
  }

  async function uploadPDF() {
    if (!file || uploading) return
    setUploading(true)
    setStatus({ type: "loading", text: "Uploading and indexing document…" })
    try {
      const form = new FormData()
      form.append("file", file)
      const res = await axios.post(API + "/upload", form)
      setStatus({ type: "success", text: res.data.message || "Document indexed successfully." })
      setDocReady(true)
    } catch {
      setStatus({ type: "error", text: "Upload failed. Is the backend running?" })
    } finally {
      setUploading(false)
    }
  }

  async function askQuestion() {
    const q = question.trim()
    if (!q || loading) return
    setQuestion("")
    setMessages(m => [...m, { role: "user", text: q, id: `u-${Date.now()}` }])
    setLoading(true)
    try {
      const res = await axios.post(API + "/ask", { question: q })
      setMessages(m => [...m, { role: "ai", text: res.data.answer, id: `a-${Date.now()}` }])
    } catch {
      setMessages(m => [...m, { role: "ai", text: "Something went wrong answering that question. Please try again.", id: `a-${Date.now()}`, error: true }])
    } finally {
      setLoading(false)
    }
  }

  function onInputKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      askQuestion()
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark"><IconLogo /></div>
          <div className="brand-text">
            <span className="brand-title">AskMyDocs</span>
            <span className="brand-subtitle">Local RAG document assistant</span>
          </div>
        </div>
        <div className="header-right">
          <span className={`status-pill ${docReady ? "ready" : ""}`}>
            <span className="dot" />
            {docReady ? "Document indexed" : "No document loaded"}
          </span>
        </div>
      </header>

      <main className="app-main">
        <aside className="sidebar">
          <div className="card">
            <div className="card-header">
              <p className="card-title">Document</p>
            </div>
            <div className="card-body">
              <div
                className={`dropzone ${dragActive ? "active" : ""}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={e => { e.preventDefault(); setDragActive(true) }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
              >
                <div className="dropzone-icon"><IconUpload /></div>
                <p className="dropzone-title">Drop your PDF here</p>
                <p className="dropzone-hint">or click to browse</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={e => handleFileSelect(e.target.files[0])}
                  style={{ display: "none" }}
                />
              </div>

              {file && (
                <div className="file-chip">
                  <div className="file-chip-icon"><IconPdf /></div>
                  <div className="file-chip-info">
                    <div className="file-chip-name">{file.name}</div>
                    <div className="file-chip-size">{formatBytes(file.size)}</div>
                  </div>
                  <button
                    className="file-chip-remove"
                    onClick={() => { setFile(null); setStatus(null) }}
                    aria-label="Remove file"
                  >
                    <IconClose />
                  </button>
                </div>
              )}

              <button className="btn btn-primary" onClick={uploadPDF} disabled={!file || uploading}>
                {uploading && <span className="spinner" />}
                {uploading ? "Indexing…" : "Upload & Index"}
              </button>

              {status && (
                <div className={`inline-banner ${status.type}`}>
                  {status.type === "success" && <IconCheck />}
                  {status.type === "error" && <IconAlert />}
                  {status.type === "loading" && <span className="spinner dark" />}
                  <span>{status.text}</span>
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <p className="card-title">How it works</p>
            </div>
            <div className="card-body">
              <ol className="steps">
                {STEPS.map((text, i) => (
                  <li className="step" key={i}>
                    <span className="step-index">{i + 1}</span>
                    <span className="step-text">{text}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="chat-panel-header">
            <div>
              <p className="chat-panel-title">Conversation</p>
              <p className="chat-panel-subtitle">
                {docReady ? "Ask anything about your uploaded document" : "Upload a document to get started"}
              </p>
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && !loading && (
              <div className="chat-empty">
                <div className="chat-empty-icon"><IconChat /></div>
                <p className="chat-empty-title">No messages yet</p>
                <p className="chat-empty-text">
                  {docReady
                    ? "Ask a question below and the AI will answer using only your document's content."
                    : "Upload and index a PDF from the panel on the left, then start asking questions."}
                </p>
              </div>
            )}

            {messages.map(m => (
              <div className={`message-row ${m.role}`} key={m.id}>
                <div className={`avatar ${m.role}`}>{m.role === "user" ? "You" : "AI"}</div>
                <div className={`bubble ${m.error ? "error" : ""}`}>{m.text}</div>
              </div>
            ))}

            {loading && (
              <div className="message-row ai">
                <div className="avatar ai">AI</div>
                <div className="bubble">
                  <span className="typing-indicator"><span /><span /><span /></span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-bar">
            <textarea
              className="chat-input"
              rows={1}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={onInputKeyDown}
              placeholder={docReady ? "Ask a question about your PDF…" : "Upload a document first…"}
              disabled={!docReady || loading}
            />
            <button
              className="send-btn"
              onClick={askQuestion}
              disabled={!docReady || loading || !question.trim()}
              aria-label="Send question"
            >
              <IconSend />
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}
