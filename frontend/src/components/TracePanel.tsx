import { CodeBlock } from './CodeBlock'
import { RouteBadge } from './RouteBadge'
import type { ChatResponse } from '../types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'

type TracePanelProps = {
  answer: ChatResponse | null
}

export function TracePanel({ answer }: TracePanelProps) {
  const normalizeMathDelimiters = (text: string) =>
    text
      .replace(/\\\[/g, '$$')
      .replace(/\\\]/g, '$$')
      .replace(/\\\(/g, '$')
      .replace(/\\\)/g, '$')

  return (
    <aside className="panel trace-panel">
      <h3>Answer Trace</h3>
      <div className="trace-section">
        <p className="trace-label">Route</p>
        <RouteBadge route={answer?.route ?? 'unknown'} />
      </div>
      <div className="trace-section">
        <p className="trace-label">Route Reason</p>
        <p>{answer?.route_reason ?? 'Route reasoning will appear after your first question.'}</p>
      </div>
      <div className="trace-section">
        <p className="trace-label">Sources</p>
        {answer?.sources?.length ? (
          <ul className="source-list">
            {answer.sources.map((source) => (
              <li key={source}>{source}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">No document sources for this route.</p>
        )}
      </div>
      <div className="trace-section">
        <p className="trace-label">Generated SQL Query</p>
        <CodeBlock code={answer?.sql_query ?? ''} language="sql" emptyMessage="No SQL query for this route." />
      </div>
      <details className="trace-section retrieved-context-section" open>
        <summary>Retrieved Context</summary>
        <div className="retrieved-context-body">
          {answer?.retrieved_context?.length ? (
            <div className="context-list-scroll">
              <div className="context-list">
              {answer.retrieved_context.map((item, index) => (
                <article key={`${item.source ?? 'source'}-${index}`} className="context-item">
                  <p className="context-title">
                    {index + 1}. {item.source ?? 'unknown source'}
                  </p>
                  <p className="muted">
                    chunk {item.chunk_index ?? 'n/a'}
                    {typeof item.score === 'number' ? ` | score ${item.score.toFixed(3)}` : ''}
                  </p>
                  <div className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
                      {normalizeMathDelimiters(item.text ?? '')}
                    </ReactMarkdown>
                  </div>
                </article>
              ))}
              </div>
            </div>
          ) : (
            <p className="muted">No retrieved document context for this route.</p>
          )}
        </div>
      </details>
      {answer?.error ? (
        <div className="trace-section error-box">
          <p className="trace-label">Error</p>
          <p>{answer.error}</p>
        </div>
      ) : null}
    </aside>
  )
}
