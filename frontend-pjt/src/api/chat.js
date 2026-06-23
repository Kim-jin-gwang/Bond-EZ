import { apiPost } from './client'

const SESSION_STORAGE_KEY = 'bond_chat_session_id'

export function getChatSessionId() {
  const savedSessionId = sessionStorage.getItem(SESSION_STORAGE_KEY)
  if (savedSessionId) return savedSessionId

  const sessionId = crypto.randomUUID()
  sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId)
  return sessionId
}

export function sendChatMessage(message) {
  return apiPost('/chat', {
    session_id: getChatSessionId(),
    message,
  })
}

