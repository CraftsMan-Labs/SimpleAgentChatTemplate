import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  createChatCompletion,
  createChatCompletionStream,
  listModels,
} from '../api/openai'
import type { ChatMessage, ModelCard } from '../types/openai'


export const useChatStore = defineStore('chat', () => {
  const models = ref<ModelCard[]>([])
  const selectedModel = ref('')
  const messages = ref<ChatMessage[]>([])
  const input = ref('')
  const loading = ref(false)
  const conversationId = ref<string | undefined>()
  const theme = ref<'dark' | 'light'>('dark')

  async function init(): Promise<void> {
    const response = await listModels()
    models.value = response.data
    if (!selectedModel.value && models.value.length > 0) {
      const firstModel = models.value[0]
      if (firstModel) {
        selectedModel.value = firstModel.id
      }
    }
  }

  function toggleTheme(): void {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('chat-theme', theme.value)
  }

  function loadTheme(): void {
    const saved = localStorage.getItem('chat-theme')
    if (saved === 'dark' || saved === 'light') {
      theme.value = saved
    }
  }

  async function send(stream = true): Promise<void> {
    if (!input.value.trim() || !selectedModel.value || loading.value) {
      return
    }

    const userText = input.value.trim()
    input.value = ''
    messages.value.push({ role: 'user', content: userText })
    loading.value = true

    const payloadMessages = [...messages.value]

    if (!stream) {
      const { completion, conversationId: cid } = await createChatCompletion(
        {
          model: selectedModel.value,
          messages: payloadMessages,
          stream: false,
        },
        conversationId.value,
      )
      conversationId.value = cid
      const content = completion.choices[0]?.message.content ?? ''
      messages.value.push({ role: 'assistant', content })
      loading.value = false
      return
    }

    messages.value.push({ role: 'assistant', content: '' })
    await createChatCompletionStream(
      {
        model: selectedModel.value,
        messages: payloadMessages,
        stream: true,
      },
      (delta) => {
        const last = messages.value[messages.value.length - 1]
        if (last?.role === 'assistant') {
          last.content += delta
        }
      },
      (cid) => {
        conversationId.value = cid
      },
      conversationId.value,
    )
    loading.value = false
  }

  return {
    models,
    selectedModel,
    messages,
    input,
    loading,
    theme,
    conversationId,
    init,
    toggleTheme,
    loadTheme,
    send,
  }
})
