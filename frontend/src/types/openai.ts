export type ChatRole = 'system' | 'user' | 'assistant' | 'tool'

export interface ChatMessage {
  role: ChatRole
  content: string
}

export interface ModelCard {
  id: string
  object: 'model'
  created: number
  owned_by: string
  metadata: Record<string, unknown>
}

export interface ModelsResponse {
  object: 'list'
  data: ModelCard[]
}

export interface ChatCompletionRequest {
  model: string
  messages: ChatMessage[]
  stream: boolean
  user?: string
}

export interface ChatCompletionResponse {
  id: string
  object: 'chat.completion'
  created: number
  model: string
  choices: {
    index: number
    message: { role: 'assistant'; content: string }
    finish_reason: string | null
  }[]
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  metadata?: {
    conversation_id?: string
    [key: string]: unknown
  }
}
