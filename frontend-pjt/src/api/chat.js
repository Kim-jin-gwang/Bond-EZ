import { API_BASE_URL } from './client'

const SESSION_STORAGE_KEY = 'bond_chat_session_id'

export function getChatSessionId() {
  const savedSessionId = sessionStorage.getItem(SESSION_STORAGE_KEY)
  if (savedSessionId) return savedSessionId

  const sessionId = crypto.randomUUID()
  sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId)
  return sessionId
}

export async function sendChatMessageStream(message, currentPage = null, pageParams = {}) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({
      session_id: getChatSessionId(),
      message,
      current_page: currentPage,
      page_params: pageParams,
    }),
  })

  if (!response.ok) {
    throw new Error('채팅 답변 요청에 실패했습니다.')
  }

  return response.body.getReader()
}

