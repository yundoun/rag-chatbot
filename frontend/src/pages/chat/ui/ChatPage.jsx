import { useState } from 'react'
import { Sidebar } from '@widgets/sidebar'
import { ChatPanel } from '@widgets/chat-panel'

export function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-light-bg text-light-text-primary">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <ChatPanel
          onMenuClick={() => setSidebarOpen(true)}
        />
      </main>
    </div>
  )
}

export default ChatPage
