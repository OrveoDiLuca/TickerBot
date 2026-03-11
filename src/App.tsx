import Sidebar from './components/SideBar'
import Chat from './components/Chat'

function App() {
  return (
    <div
      className="flex h-screen w-screen overflow-hidden p-4 gap-4"
      style={{ backgroundColor: '#101622' }}
    >
      <Sidebar />
      <Chat />
    </div>
  )
}

export default App
