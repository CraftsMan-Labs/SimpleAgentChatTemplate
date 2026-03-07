import type {
  ChatCompletionChunk,
  ChatCompletionResponse,
  ModelsResponse,
  OpenAIErrorResponse,
} from '../types/openai'

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function decodeModelsResponse(value: unknown): ModelsResponse {
  if (!isObject(value) || !Array.isArray(value.data)) {
    throw new Error('Invalid models response payload')
  }
  return value as unknown as ModelsResponse
}

export function decodeChatCompletionResponse(value: unknown): ChatCompletionResponse {
  if (!isObject(value) || !Array.isArray(value.choices)) {
    throw new Error('Invalid chat completion response payload')
  }
  return value as unknown as ChatCompletionResponse
}

export function decodeOpenAIError(value: unknown): OpenAIErrorResponse | null {
  if (!isObject(value)) {
    return null
  }
  return value as OpenAIErrorResponse
}

export function decodeChatChunk(value: unknown): ChatCompletionChunk {
  if (!isObject(value) || !Array.isArray(value.choices)) {
    throw new Error('Invalid stream chunk payload')
  }
  return value as unknown as ChatCompletionChunk
}
