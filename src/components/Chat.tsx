import { useState, useRef, useEffect } from "react"
import type { Message } from "../types"
import { v4 as uuidv4 } from 'uuid'
import { BotIcon, SendIcon } from "../helpers/Icons"
import { dataAgent } from "../services/dataAgent"


const Chat = () => {
  const [message, setMessage] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [message, isLoading])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value)
  }

  const handleSend = async () => {
    const trimmedMessage = inputMessage.trim()
    if (!trimmedMessage || isLoading) return

    setMessage((prev) => [...prev, { id: uuidv4(), role: 'user', text: trimmedMessage }])
    setInputMessage('')
    setIsLoading(true)

    try {
      const botText = await dataAgent(trimmedMessage)
      setMessage((prev) => [...prev, { id: uuidv4(), role: 'bot', text: botText }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSend()
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

        {/* Estado vacío */}
        {message.length === 0 && !isLoading && (
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

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex items-start gap-3">
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
              className="px-4 py-3 rounded-2xl rounded-tl-sm text-sm animate-pulse"
              style={{
                backgroundColor: '#1a2436',
                border: '1px solid #222f47',
                color: '#94a3b8',
              }}
            >
              ...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
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
            onKeyDown={handleKeyDown}
            placeholder="Ask about stocks, earnings, or market trende. E.g., 'What is the current stock price of AAPL?'"
            className="flex-1 bg-transparent border-none outline-none text-sm py-3"
            style={{ color: '#e2e8f0' }}
          />
          <div className="flex items-center gap-2 ml-2">
            <button
              onClick={handleSend}
              disabled={isLoading}
              className="w-8 h-8 rounded-xl flex items-center justify-center text-white shadow-lg transition-opacity hover:opacity-90 hover:cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
              style={{ backgroundColor: inputMessage.trim() && !isLoading ? '#2b6cee' : '#1e2a40' }}
            >
              <SendIcon />
            </button>
          </div>
        </div>

      </div>
    </div>
  )
}
export default Chat
