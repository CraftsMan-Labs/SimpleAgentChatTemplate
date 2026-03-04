import type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  ModelsResponse,
} from '../types/openai'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function listModels(): Promise<ModelsResponse> {
  const response = await fetch(`${API_BASE}/v1/models`)
  if (!response.ok) {
    throw new Error(`Failed to load models: ${response.status}`)
  }
  return (await response.json()) as ModelsResponse
}

export async function createChatCompletion(
  payload: ChatCompletionRequest,
  conversationId?: string,
): Promise<{ completion: ChatCompletionResponse; conversationId?: string }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (conversationId) {
    headers['X-Conversation-Id'] = conversationId
  }
  const response = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.error?.message ?? `Chat request failed: ${response.status}`)
  }
  const completion = (await response.json()) as ChatCompletionResponse
  const cid = response.headers.get('X-Conversation-Id') ?? completion.metadata?.conversation_id
  return { completion, conversationId: cid ?? undefined }
}

export async function createChatCompletionStream(
  payload: ChatCompletionRequest,
  onDelta: (delta: string) => void,
  onConversationId: (conversationId: string) => void,
  conversationId?: string,
): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (conversationId) {
    headers['X-Conversation-Id'] = conversationId
  }

  const response = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ ...payload, stream: true }),
  })
  if (!response.ok || !response.body) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.error?.message ?? `Stream request failed: ${response.status}`)
  }

  const cid = response.headers.get('X-Conversation-Id')
  if (cid) {
    onConversationId(cid)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) {
        continue
      }
      const payloadText = line.slice(6).trim()
      if (payloadText === '[DONE]') {
        return
      }
      const parsed = JSON.parse(payloadText) as {
        choices?: Array<{ delta?: { content?: string } }>
      }
      const delta = parsed.choices?.[0]?.delta?.content
      if (delta) {
        onDelta(delta)
      }
    }
  }
}
