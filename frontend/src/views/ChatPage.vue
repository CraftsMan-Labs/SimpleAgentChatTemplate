<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useChatStore } from '../stores/chat'

const store = useChatStore()

const rootClass = computed(() => `theme-${store.theme}`)
const threadTitle = computed(() =>
  store.selectedModel ? `Thread: ${store.selectedModel.replace('yaml/', '')}` : 'Thread: Select model',
)

onMounted(async () => {
  store.loadTheme()
  await store.init()
})

async function onSend(): Promise<void> {
  try {
    await store.send(true)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Request failed'
    store.messages.push({ role: 'assistant', content: `Error: ${message}` })
    store.loading = false
  }
}
</script>

<template>
  <main class="chat-app" :class="rootClass">
    <aside class="sidebar">
      <section class="sidebar-top">
        <div class="brand-row">
          <div class="logo-dot"></div>
          <h1>Craftsman Chat</h1>
        </div>
        <p class="label">Workspace</p>
        <nav class="nav-list">
          <button class="nav-item">Discover</button>
          <button class="nav-item">Spaces</button>
          <button class="nav-item">Library</button>
          <button class="nav-item active">Recents</button>
        </nav>
      </section>
      <div class="avatar"></div>
    </aside>

    <section class="main-pane">
      <header class="top-bar">
        <div class="tabs">
          <span class="active-tab">Research</span>
          <span>Compose</span>
        </div>
        <div class="actions">
          <select v-model="store.selectedModel">
            <option v-for="model in store.models" :key="model.id" :value="model.id">{{ model.id }}</option>
          </select>
          <button class="theme-btn" @click="store.toggleTheme">{{ store.theme === 'dark' ? 'Light' : 'Dark' }}</button>
        </div>
      </header>

      <div class="thread-meta">
        <span class="chip">{{ threadTitle }}</span>
        <span class="chip">Mode: Balanced</span>
        <span class="chip">Updated: just now</span>
      </div>

      <div class="feed">
        <article v-for="(message, index) in store.messages" :key="`${index}-${message.role}`" :class="['message-card', message.role]">
          <p class="message-role">{{ message.role === 'user' ? 'Prompt' : 'Assistant' }}</p>
          <p class="message-content">{{ message.content }}</p>
        </article>
      </div>

      <footer class="composer-wrap">
        <textarea
          v-model="store.input"
          placeholder="Ask a follow-up..."
          :disabled="store.loading"
          @keydown.enter.exact.prevent="onSend"
        ></textarea>
        <button class="send-btn" :disabled="store.loading || !store.input.trim()" @click="onSend">
          {{ store.loading ? 'Sending...' : 'Send' }}
        </button>
      </footer>
    </section>
  </main>
</template>
