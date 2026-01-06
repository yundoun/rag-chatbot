import { useState } from 'react'
import ChatContainer from './components/ChatContainer'

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold text-gray-800">
            📚 RAG 챗봇
          </h1>
          <p className="text-sm text-gray-500">
            내부 문서를 검색하여 질문에 답변합니다
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        <ChatContainer />
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-2 text-center text-xs text-gray-400">
          RAG Chatbot v1.0.0 | 답변은 내부 문서를 기반으로 생성됩니다
        </div>
      </footer>
    </div>
  )
}

export default App
