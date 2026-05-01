import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

type CodeBlockProps = {
  code: string
  language?: string
  emptyMessage?: string
}

export function CodeBlock({ code, language = '', emptyMessage = 'No code.' }: CodeBlockProps) {
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

  if (!code?.trim()) {
    return <p className="muted">{emptyMessage}</p>
  }

  return (
    <div className="code-block">
      <SyntaxHighlighter
        language={language || 'text'}
        style={cleanTheme}
        customStyle={{ margin: 0, borderRadius: '12px', background: '#050a18', padding: '12px' }}
        wrapLongLines={false}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
