<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRoute } from 'vue-router'
import { sendChatMessage } from '../../api/chat'
import { useNavigation } from '../../composables/useNavigation'

const route = useRoute()
const { navigate } = useNavigation()

const isOpen = ref(false)
const chatMode = ref('normal') // 'normal', 'large', 'sidebar'
const chatWidth = ref(400) // Default width in pixels for sidebar mode
const isResizing = ref(false)
const input = ref('')
const isSending = ref(false)
const errorMessage = ref('')
const messages = ref([
  {
    id: 'welcome',
    role: 'assistant',
    content: '안녕하세요. 채권 개념, 수익률, 듀레이션, 신용등급에 대해 질문해보세요.',
    sources: [],
    recommendedQuestions: [
      '듀레이션이 무엇인가요?',
      '만기수익률(YTM)은 무엇인가요?',
      '신용등급은 어떻게 결정되나요?'
    ],
    navigationRecommendations: []
  },
])
const messageList = ref(null)

const canSend = computed(() => input.value.trim().length > 0 && !isSending.value)

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(scrollToBottom)
  }
}

async function handleSubmit(customText = null) {
  const text = customText !== null ? customText.trim() : input.value.trim()
  if (!text || isSending.value) return

  errorMessage.value = ''
  if (customText === null) {
    input.value = ''
  }

  messages.value.push({
    id: crypto.randomUUID(),
    role: 'user',
    content: text,
    sources: [],
    recommendedQuestions: [],
    navigationRecommendations: []
  })

  isSending.value = true
  await nextTick(scrollToBottom)

  try {
    const currentPage = route.meta.page || 'home'
    const pageParams = route.params || {}
    const result = await sendChatMessage(text, currentPage, pageParams)
    
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'assistant',
      content: result.answer,
      sources: result.sources || [],
      recommendedQuestions: result.recommended_questions || [],
      navigationRecommendations: result.navigation_recommendations || []
    })
  } catch (error) {
    errorMessage.value = error.message || '답변을 불러오지 못했습니다.'
  } finally {
    isSending.value = false
    await nextTick(scrollToBottom)
  }
}

function handleNavigation(nav) {
  navigate(nav.page, nav.payload)
}

function startResize(e) {
  e.preventDefault()
  isResizing.value = true
  
  const initialWidth = chatWidth.value
  const startX = e.clientX

  function doResize(moveEvent) {
    if (!isResizing.value) return
    const deltaX = startX - moveEvent.clientX
    const newWidth = initialWidth + deltaX
    // Limit resizing width: Min 280px, Max 60% of viewport width
    if (newWidth >= 280 && newWidth <= window.innerWidth * 0.6) {
      chatWidth.value = newWidth
    }
  }

  function stopResize() {
    isResizing.value = false
    window.removeEventListener('mousemove', doResize)
    window.removeEventListener('mouseup', stopResize)
  }

  window.addEventListener('mousemove', doResize)
  window.addEventListener('mouseup', stopResize)
}

function scrollToBottom() {
  if (!messageList.value) return
  messageList.value.scrollTop = messageList.value.scrollHeight
}
</script>

<template>
  <section 
    v-if="isOpen" 
    :class="['bond-chat-panel', 'bond-chat-mode-' + chatMode, { 'is-resizing': isResizing }]" 
    :style="{ width: chatMode === 'sidebar' ? chatWidth + 'px' : '' }"
    aria-label="채권 AI 챗봇"
  >
    <!-- Left resizer handle (only active in sidebar mode) -->
    <div 
      v-if="chatMode === 'sidebar'" 
      class="sidebar-resizer" 
      @mousedown="startResize"
    ></div>

    <header class="bond-chat-header">
      <div class="bond-chat-header-title">
        <span>Bond AI</span>
        <strong>채권 챗봇</strong>
      </div>
      <div class="bond-chat-header-controls">
        <button
          type="button"
          class="ctrl-btn"
          :class="{ active: chatMode === 'normal' }"
          title="기본 크기"
          @click="chatMode = 'normal'"
        >
          기본
        </button>
        <button
          type="button"
          class="ctrl-btn"
          :class="{ active: chatMode === 'large' }"
          title="크게 보기"
          @click="chatMode = 'large'"
        >
          확대
        </button>
        <button
          type="button"
          class="ctrl-btn"
          :class="{ active: chatMode === 'sidebar' }"
          title="사이드바로 고정"
          @click="chatMode = 'sidebar'"
        >
          사이드바
        </button>
        <button
          type="button"
          class="ctrl-btn close-btn"
          aria-label="채팅창 닫기"
          @click="isOpen = false"
        >
          x
        </button>
      </div>
    </header>

    <div ref="messageList" class="bond-chat-messages" aria-live="polite">
      <article
        v-for="message in messages"
        :key="message.id"
        class="bond-chat-message"
        :class="`bond-chat-message-${message.role}`"
      >
        <p>{{ message.content }}</p>
        
        <!-- Sources -->
        <ul v-if="message.sources?.length" class="bond-chat-sources">
          <li v-for="source in message.sources" :key="`${source.title}-${source.page || ''}`">
            {{ source.title }}<span v-if="source.page"> p.{{ source.page }}</span>
          </li>
        </ul>

        <!-- Navigation Recommendations -->
        <div v-if="message.navigationRecommendations?.length" class="bond-chat-navigation-actions">
          <button
            v-for="nav in message.navigationRecommendations"
            :key="nav.label"
            type="button"
            class="bond-chat-nav-button"
            @click="handleNavigation(nav)"
          >
            {{ nav.label }}
          </button>
        </div>

        <!-- Recommended follow-up questions -->
        <div v-if="message.recommendedQuestions?.length" class="bond-chat-recommended-questions">
          <button
            v-for="question in message.recommendedQuestions"
            :key="question"
            type="button"
            class="bond-chat-question-chip"
            @click="handleSubmit(question)"
          >
            {{ question }}
          </button>
        </div>
      </article>

      <div v-if="isSending" class="bond-chat-status">답변을 생성하는 중입니다...</div>
      <div v-if="errorMessage" class="bond-chat-error">{{ errorMessage }}</div>
    </div>

    <form class="bond-chat-form" @submit.prevent="handleSubmit(null)">
      <label for="bond-chat-input" class="sr-only">채권 질문 입력</label>
      <input
        id="bond-chat-input"
        v-model="input"
        type="text"
        placeholder="채권에 대해 질문하세요"
        autocomplete="off"
      />
      <button type="submit" :disabled="!canSend">전송</button>
    </form>
  </section>

  <!-- AI Toggle button hidden when sidebar mode is active and chatbot is open -->
  <button
    v-if="!(isOpen && chatMode === 'sidebar')"
    type="button"
    class="bond-chat-toggle"
    :aria-expanded="isOpen"
    aria-label="채권 챗봇 열기"
    @click="toggleChat"
  >
    AI
  </button>
</template>
