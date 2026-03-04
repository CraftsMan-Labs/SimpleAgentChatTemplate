import { createRouter, createWebHistory } from 'vue-router'

import ChatPage from './views/ChatPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: ChatPage }],
})

export default router
