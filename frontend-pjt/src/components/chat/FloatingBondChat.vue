<script setup>
import { computed, nextTick, ref } from 'vue'
import { sendChatMessage } from '../../api/chat'

const isOpen = ref(false)
const input = ref('')
const isSending = ref(false)
const errorMessage = ref('')
const messages = ref([
  {
    id: 'welcome',
    role: 'assistant',
    content: '안녕하세요. 채권 개념, 수익률, 듀레이션, 신용등급에 대해 질문해보세요.',
    sources: [],
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

async function handleSubmit() {
  const text = input.value.trim()
  if (!text || isSending.value) return

  errorMessage.value = ''
  input.value = ''
  messages.value.push({
    id: crypto.randomUUID(),
    role: 'user',
    content: text,
    sources: [],
  })

  isSending.value = true
  await nextTick(scrollToBottom)

  try {
    const result = await sendChatMessage(text)
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'assistant',
      content: result.answer,
      sources: result.sources || [],
    })
  } catch (error) {
    errorMessage.value = error.message || '답변을 불러오지 못했습니다.'
  } finally {
    isSending.value = false
    await nextTick(scrollToBottom)
  }
}

function scrollToBottom() {
  if (!messageList.value) return
  messageList.value.scrollTop = messageList.value.scrollHeight
}
</script>

<template>
  <section v-if="isOpen" class="bond-chat-panel" aria-label="채권 AI 챗봇">
    <header class="bond-chat-header">
      <div>
        <span>Bond AI</span>
        <strong>채권 챗봇</strong>
      </div>
      <button type="button" class="bond-chat-icon-button" aria-label="채팅창 닫기" @click="isOpen = false">
        x
      </button>
    </header>

    <div ref="messageList" class="bond-chat-messages" aria-live="polite">
      <article
        v-for="message in messages"
        :key="message.id"
        class="bond-chat-message"
        :class="`bond-chat-message-${message.role}`"
      >
        <p>{{ message.content }}</p>
        <ul v-if="message.sources?.length" class="bond-chat-sources">
          <li v-for="source in message.sources" :key="`${source.title}-${source.page || ''}`">
            {{ source.title }}<span v-if="source.page"> p.{{ source.page }}</span>
          </li>
        </ul>
      </article>

      <div v-if="isSending" class="bond-chat-status">답변을 생성하는 중입니다...</div>
      <div v-if="errorMessage" class="bond-chat-error">{{ errorMessage }}</div>
    </div>

    <form class="bond-chat-form" @submit.prevent="handleSubmit">
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

  <button
    type="button"
    class="bond-chat-toggle"
    :aria-expanded="isOpen"
    aria-label="채권 챗봇 열기"
    @click="toggleChat"
  >
    AI
  </button>
</template>
