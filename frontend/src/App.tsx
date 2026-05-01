import { useState } from 'react'
import { postChat } from './api'
import { ChatPanel } from './components/ChatPanel'
import { TracePanel } from './components/TracePanel'
import type { ChatResponse } from './types'
import './styles.css'

type ChatTurn = {
  id: string
  question: string
  pending: boolean
  response: ChatResponse | null
}

function App() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState<ChatTurn[]>([])
  const [loading, setLoading] = useState(false)

  const submitQuestion = async (forcedQuestion?: string) => {
    const cleanQuestion = (forcedQuestion ?? question).trim()
    if (!cleanQuestion || loading) return

    const turnId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    setHistory((prev) => [
      ...prev,
      { id: turnId, question: cleanQuestion, pending: true, response: null },
    ])
    setLoading(true)
    try {
      const response = await postChat({ question: cleanQuestion })
      setHistory((prev) =>
        prev.map((turn) =>
          turn.id === turnId ? { ...turn, pending: false, response } : turn,
        ),
      )
      if (!forcedQuestion) {
        setQuestion('')
      }
    } catch (error) {
      const errorResponse: ChatResponse = {
        question: cleanQuestion,
        route: 'error',
        route_reason: 'Frontend request failure.',
        answer:
          'The UI could not reach the backend API. Confirm FastAPI is running and VITE_API_BASE_URL is correct.',
        sources: [],
        sql_query: null,
        retrieved_context: [],
        error: error instanceof Error ? error.message : 'Unknown frontend error.',
      }
      setHistory((prev) =>
        prev.map((turn) =>
          turn.id === turnId ? { ...turn, pending: false, response: errorResponse } : turn,
        ),
      )
    } finally {
      setLoading(false)
    }
  }

  const latestAnswer =
    [...history]
      .reverse()
      .find((turn) => !turn.pending && turn.response)?.response ?? null

  return (
    <div className="app-shell">
      <header className="hero">
        <h1>Business Intelligence AI Assistant</h1>
        <p>Local-first RAG + SQL assistant for synthetic payment operations data</p>
      </header>
      <main className="layout">
        <ChatPanel
          question={question}
          setQuestion={setQuestion}
          history={history}
          loading={loading}
          onSubmit={() => submitQuestion()}
        />
        <TracePanel answer={latestAnswer} />
      </main>
    </div>
  )
}

export default App
