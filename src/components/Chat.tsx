import { useState, useRef, useEffect } from "react"
import type { Conversation } from "../types"
import { v4 as uuidv4 } from 'uuid'
import { BotIcon, SendIcon } from "../helpers/Icons"
import StockCard from "./StockCard"
import { callBackend } from "../helpers/functions"
 


const Chat = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]) //Estado donde se almacenan las conversaciones entre el usuario y el bot. Cada conversación incluye el texto del usuario, la respuesta del bot y los datos de acciones relacionados (si los hay).
  const [inputMessage, setInputMessage] = useState('') //Estado para controlar el valor del campo de entrada del usuario. 
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null) //Referencia a un elemento div al final de la lista de conversaciones. Se utiliza para desplazar automáticamente la vista hacia abajo cuando se agregan nuevas conversaciones o mientras el bot está "escribiendo" una respuesta.

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversations, isLoading]) //Este useEffect se ejecuta cada vez que cambian las conversaciones o el estado de carga. Su función es basicamente desplazar la vista hacia el elemento referenciado por el bottonRef. 

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value)
  }

  const handleSend = async () => {
    const trimmedMessage = inputMessage.trim()
    if (!trimmedMessage || isLoading) return

    const id = uuidv4()
    setConversations((prev) => [...prev, { id, userText: trimmedMessage, botText: null, stockData: null }])
    setInputMessage('')
    setIsLoading(true)

    try {
      const { botText, stockData } = await callBackend(trimmedMessage) //Esta linea aplica un destructuring al mensaje del usuario, y lo divide en el mensaje del bot y el stock que solicita el usuario. 
      setConversations((prev) =>
        prev.map((conv) => conv.id === id ? { ...conv, botText, stockData } : conv)
      )
    }catch{
      //Manejo de errores. 
      setConversations((prev) => prev.filter((conv) => conv.id !== id))
      setErrorMessage("Hubo error con el servidor. Porfavor Intenta de nuevo.")
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
        {conversations.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full gap-3 opacity-40">
            <svg className="w-10 h-10 fill-current text-slate-500" viewBox="0 0 24 24">
              <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" />
            </svg>
            <p className="text-slate-500 text-sm">Pregunta sobre cualquier acción o empresa</p>
          </div>
        )}

        {/* Conversaciones */}
        {conversations.map((conv) => (
          <div key={conv.id} className="flex flex-col gap-4">
            {/* Mensaje del usuario */}
            <div className="flex justify-end items-end gap-3">
              <div className="flex flex-col items-end gap-1 max-w-[70%]">
                <div
                  className="text-white px-5 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed shadow-lg"
                  style={{ backgroundColor: '#2b6cee' }}
                >
                  {conv.userText}
                </div>
              </div>
            </div>

            {/* Respuesta del bot */}
            {conv.botText !== null && (
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
                <div className="flex flex-col max-w-[75%]">
                  <div
                    className="px-4 py-3 rounded-2xl rounded-tl-sm text-sm leading-relaxed"
                    style={{
                      backgroundColor: '#1a2436',
                      border: '1px solid #222f47',
                      color: '#94a3b8',
                    }}
                  >
                    {conv.botText}
                  </div>
                  {conv.stockData && (
                    <StockCard data={conv.stockData} />
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

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

      {errorMessage && (
        <div 
          className="mx-4 mb-2 px-4 py-3 rounded-xl text-sm flex items-center justify-between"
          style={{ backgroundColor: '#2d1b1b', border: '1px solid #7f1d1d', color: '#f87171' }}
          >
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="ml-4 hover:opacity-70 cursor-pointer">x</button>
        </div>
        
      )}

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
