import type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  ModelsResponse,
} from '../types/openai'
import { streamSseData } from './sse'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

function buildChatHeaders(conversationId?: string): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (conversationId) {
    headers['X-Conversation-Id'] = conversationId
  }
  return headers
}

async function parseErrorMessage(response: Response, fallback: string): Promise<string> {
  const err = await response.json().catch(() => null)
  return err?.error?.message ?? fallback
}

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
  const response = await fetch(`${API_BASE}/v1/chat/completions/stream`, {
    method: 'POST',
    headers: buildChatHeaders(conversationId),
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response, `Chat request failed: ${response.status}`))
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
  const response = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: 'POST',
    headers: buildChatHeaders(conversationId),
    body: JSON.stringify({ ...payload, stream: true }),
  })
  if (!response.ok || !response.body) {
    throw new Error(await parseErrorMessage(response, `Stream request failed: ${response.status}`))
  }

  const cid = response.headers.get('X-Conversation-Id')
  if (cid) {
    onConversationId(cid)
  }

  await streamSseData(response, (payloadText) => {
    if (payloadText === '[DONE]') {
      return true
    }
    const parsed = JSON.parse(payloadText) as {
      choices?: Array<{ delta?: { content?: string } }>
    }
    const delta = parsed.choices?.[0]?.delta?.content
    if (delta) {
      onDelta(delta)
    }
  })
}
