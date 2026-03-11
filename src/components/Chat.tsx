import { useState } from "react"
import type { Message } from "../types"
import { v4 as uuidv4 } from 'uuid'


const Chat = () => {
  const [message, setMessage] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value)
  }

  const handleSend = () => {
    const trimmedMessage = inputMessage.trim()
    if(!trimmedMessage) return //No envia mensaje si está vacío
    setMessage((prev) => [...prev, {id: uuidv4(), role: 'user', text: trimmedMessage}])
    setInputMessage('')
  }
  return (
    <div
      className="flex-1 flex flex-col h-full rounded-2xl overflow-hidden"
      style={{ backgroundColor: '#151d2e', border: '1px solid #222f47' }}
    >
      {/* Header */}
      <header
        className="h-16 flex items-center justify-between px-6 shrink-0"
        style={{ borderBottom: '1px solid #222f47' }}
      >
      </header>

      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">

        {/* Estado vacío, si el estado se encuentra vacío, pues se mostrará el siguiente mensaje*/} 
        {message.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3 opacity-40">
            <svg className="w-10 h-10 fill-current text-slate-500" viewBox="0 0 24 24">
              <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" />
            </svg>
            <p className="text-slate-500 text-sm">Pregunta sobre cualquier acción o empresa</p>
          </div>
        )}
      {/* Renderizado dinámico de mensajes */}
        {message.map((msg) =>
          msg.role === 'user' ? (
            // Mensaje del usuario (derecha)
            <div key={msg.id} className="flex justify-end items-end gap-3">
              <div className="flex flex-col items-end gap-1 max-w-[70%]">
                <div
                  className="text-white px-5 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed shadow-lg"
                  style={{ backgroundColor: '#2b6cee' }}
                >
                  {msg.text}
                </div>
              </div>
            </div>
          ) : (
            // Mensaje del bot (izquierda)
            <div key={msg.id} className="flex items-start gap-3">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                style={{
                  backgroundColor: 'rgba(43,108,238,0.15)',
                  border: '1px solid rgba(43,108,238,0.25)',
                }}
              >
                <BotIcon />
              </div>
              <div
                className="px-4 py-3 rounded-2xl rounded-tl-sm text-sm leading-relaxed max-w-[75%]"
                style={{
                  backgroundColor: '#1a2436',
                  border: '1px solid #222f47',
                  color: '#94a3b8',
                }}
              >
                {msg.text}
              </div>
            </div>
          )
        )}
      </div>

      {/* Área de input */}
      <div className="p-4" style={{ borderTop: '1px solid #222f47' }}>
        <div
          className="flex items-center rounded-2xl overflow-hidden px-4 py-1"
          style={{ backgroundColor: '#1a2436', border: '1px solid #222f47' }}
        >
          <svg className="w-4 h-4 mr-3 shrink-0" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
          </svg>
          <input
            type="text"
            value={inputMessage}
            onChange={handleInputChange}
            // onKeyDown={handleKeyDown}
            placeholder="Ask about stocks, earnings, or market trends..."
            className="flex-1 bg-transparent border-none outline-none text-sm py-3"
            style={{ color: '#e2e8f0' }}
          />
          <div className="flex items-center gap-2 ml-2">
            <button
              onClick={handleSend}
              className="w-8 h-8 rounded-xl flex items-center justify-center text-white shadow-lg transition-opacity hover:opacity-90 hover:cursor-pointer"
              style={{ backgroundColor: inputMessage.trim() ? '#2b6cee' : '#1e2a40' }}
            >
              <SendIcon />
            </button>
          </div>
        </div>

        {/* Sugerencias rápidas */}
        <div className="mt-3 flex flex-wrap justify-center gap-2">
          {['¿Cómo va Apple hoy?', 'Earnings de NVDA', 'Noticias de Tesla'].map((s) => (
            <button
              key={s}
              // onClick={() => handleSuggestion(s)}
              className="px-3 py-1.5 rounded-full text-[11px] font-semibold transition-colors hover:text-white"
              style={{ border: '1px solid #222f47', color: '#64748b' }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ----- Íconos -----
const BotIcon = () => (
  <svg className="w-5 h-5 fill-current" style={{ color: '#2b6cee' }} viewBox="0 0 24 24">
    <path d="M20 9V7c0-1.1-.9-2-2-2h-3c0-1.66-1.34-3-3-3S9 3.34 9 5H6c-1.1 0-2 .9-2 2v2c-1.66 0-3 1.34-3 3s1.34 3 3 3v4c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-4c1.66 0 3-1.34 3-3s-1.34-3-3-3zM7 17l1.5-3h7L17 17H7zm1-6a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm6 0a1.5 1.5 0 110 3 1.5 1.5 0 010-3z" />
  </svg>
)

const SendIcon = () => (
  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
  </svg>
)

export default Chat