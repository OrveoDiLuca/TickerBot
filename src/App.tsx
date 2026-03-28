import { useState } from 'react'
import Sidebar from './components/SideBar'
import Chat from './components/Chat'
import type { Conversation } from './types'

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([])

  return (
    <div
      className="flex h-screen w-screen overflow-hidden p-4 gap-4"
      style={{ backgroundColor: '#101622' }}
    >
      <Sidebar conversations={conversations} onNewChat={() => setConversations([])} />
      <Chat conversations={conversations} setConversations={setConversations} />
    </div>
  )
}

export default App
