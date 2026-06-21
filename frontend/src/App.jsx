import { useState } from "react"
import axios from "axios"

const API = "http://localhost:8000"

export default function App() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState("")
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  async function uploadPDF() {
    if (!file) return
    setStatus("Uploading and indexing...")
    const form = new FormData()
    form.append("file", file)
    const res = await axios.post(API + "/upload", form)
    setStatus(res.data.message)
  }

  async function askQuestion() {
    if (!question.trim()) return
    const q = question
    setQuestion("")
    setMessages(m => [...m, { role: "user", text: q }])
    setLoading(true)
    const res = await axios.post(API + "/ask", { question: q })
    setMessages(m => [...m, { role: "ai", text: res.data.answer }])
    setLoading(false)
  }

  return (
    <div style={{maxWidth:680,margin:"40px auto",padding:"0 20px",
      fontFamily:"sans-serif"}}>
      <h1 style={{fontSize:24,marginBottom:8}}>AskMyDocs</h1>
      <p style={{color:"#666",marginBottom:24}}>
        Upload a PDF, then ask questions about it</p>

      <div style={{border:"1px solid #ddd",borderRadius:8,
        padding:16,marginBottom:24}}>
        <input type="file" accept=".pdf"
          onChange={e => setFile(e.target.files[0])}
          style={{marginBottom:8,display:"block"}} />
        <button onClick={uploadPDF}
          style={{padding:"8px 16px",background:"#185FA5",
            color:"white",border:"none",borderRadius:6,cursor:"pointer"}}>
          Upload PDF
        </button>
        {status && <p style={{marginTop:8,color:"#0F6E56",fontSize:14}}>
          {status}</p>}
      </div>

      <div style={{border:"1px solid #ddd",borderRadius:8,
        padding:16,minHeight:300}}>
        {messages.map((m,i) => (
          <div key={i} style={{marginBottom:12,
            textAlign: m.role==="user"?"right":"left"}}>
            <span style={{display:"inline-block",padding:"8px 12px",
              borderRadius:8,maxWidth:"80%",fontSize:14,
              background: m.role==="user"?"#185FA5":"#f0f0f0",
              color: m.role==="user"?"white":"#333"}}>
              {m.text}
            </span>
          </div>
        ))}
        {loading && <p style={{color:"#888",fontSize:14}}>
          Thinking...</p>}
      </div>

      <div style={{display:"flex",gap:8,marginTop:12}}>
        <input value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key==="Enter" && askQuestion()}
          placeholder="Ask a question about your PDF..."
          style={{flex:1,padding:"10px 12px",border:"1px solid #ddd",
            borderRadius:6,fontSize:14}} />
        <button onClick={askQuestion}
          style={{padding:"10px 16px",background:"#185FA5",
            color:"white",border:"none",borderRadius:6,cursor:"pointer"}}>
          Ask
        </button>
      </div>
    </div>
  )
}