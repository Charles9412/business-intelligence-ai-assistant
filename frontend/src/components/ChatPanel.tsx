import type { FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import type { ChatResponse } from '../types'
import { useEffect, useRef } from 'react'
import { ExampleQuestions } from './ExampleQuestions'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

type ChatPanelProps = {
  question: string
  setQuestion: (value: string) => void
  history: ChatResponse[]
  loading: boolean
  onSubmit: () => void
}

export function ChatPanel({ question, setQuestion, history, loading, onSubmit }: ChatPanelProps) {
  const cleanTheme = Object.fromEntries(
    Object.entries(oneDark).map(([key, value]) => {
      if (value && typeof value === 'object') {
        return [
          key,
          {
            ...value,
            background: 'transparent',
            backgroundColor: 'transparent',
          },
        ]
      }
      return [key, value]
    }),
  )

  const conversationRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (conversationRef.current) {
      conversationRef.current.scrollTop = conversationRef.current.scrollHeight
    }
  }, [history])

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit()
  }

  const normalizeMathDelimiters = (text: string) =>
    text
      .replace(/\\\[/g, '$$')
      .replace(/\\\]/g, '$$')
      .replace(/\\\(/g, '$')
      .replace(/\\\)/g, '$')

  const removeSqlSection = (text: string) => {
    const patterns = [
      /\n##\s*SQL Query Used[\s\S]*$/i,
      /\n###\s*SQL Query Used[\s\S]*$/i,
      /\n##\s*SQL Query[\s\S]*$/i,
      /\n###\s*SQL Query[\s\S]*$/i,
    ]
    return patterns.reduce((current, pattern) => current.replace(pattern, ''), text).trim()
  }

  const removeSourcesSection = (text: string) => {
    const patterns = [
      /\nSources:\s.*$/gim,
      /\nSource:\s.*$/gim,
    ]
    return patterns.reduce((current, pattern) => current.replace(pattern, ''), text).trim()
  }

  return (
    <section className="panel chat-panel">
      <h3>Main Answer</h3>
      <div className="conversation" ref={conversationRef}>
        {history.length ? (
          history.map((item, index) => (
            <div key={`${item.question}-${index}`} className="chat-turn">
            <article className="bubble user-bubble chat-user">
              <p className="bubble-label">User</p>
                <p>{item.question}</p>
            </article>
            <article className="bubble assistant-bubble chat-assistant">
              <p className="bubble-label">Assistant</p>
              <div className="markdown-body">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    pre({ children }) {
                      return <>{children}</>
                    },
                    code({ className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '')
                      const language = match?.[1]?.toLowerCase() ?? ''
                      const content = String(children).replace(/\n$/, '')
                      if (!match) {
                        return (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        )
                      }
                      return (
                        <div className="markdown-codeblock">
                          <SyntaxHighlighter
                            language={language === 'sql' ? 'sql' : language}
                            style={cleanTheme}
                            customStyle={{
                              margin: 0,
                              borderRadius: '12px',
                            background: '#050a18',
                            padding: '12px',
                          }}
                          wrapLongLines={false}
                        >
                          {content}
                        </SyntaxHighlighter>
                        </div>
                      )
                    },
                  }}
                >
                  {removeSourcesSection(removeSqlSection(normalizeMathDelimiters(item.answer)))}
                </ReactMarkdown>
              </div>
            </article>
            </div>
          ))
        ) : (
          <p className="muted">Ask a question to start the analysis.</p>
        )}
      </div>
      <form className="chat-form" onSubmit={submit}>
        <ExampleQuestions value={question} onSelect={setQuestion} />
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a KPI, policy, SQL analytics, or hybrid question..."
          rows={3}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Ask'}
        </button>
      </form>
    </section>
  )
}
