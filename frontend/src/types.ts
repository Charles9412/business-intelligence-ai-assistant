export type RouteType = 'rag' | 'sql' | 'hybrid' | 'error' | string

export interface RetrievedContextItem {
  text?: string
  source?: string
  chunk_index?: number
  score?: number
  distance?: number
}

export interface ChatRequest {
  question: string
}

export interface ChatResponse {
  question: string
  route: RouteType | null
  route_reason: string | null
  answer: string
  sources: string[]
  sql_query: string | null
  retrieved_context: RetrievedContextItem[]
  error: string | null
}

