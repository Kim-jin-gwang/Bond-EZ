from collections import OrderedDict

try:
    from langchain_core.chat_history import InMemoryChatMessageHistory
except ImportError:
    InMemoryChatMessageHistory = None

# 메모리 보호: 세션 수와 세션당 메시지 수를 제한한다.
# (기존에는 전역 dict에 무한 누적되어 재시작 전까지 메모리가 계속 증가했음)
MAX_SESSIONS = 500
MAX_MESSAGES_PER_SESSION = 40


class SimpleMessage:
    def __init__(self, message_type, content):
        self.type = message_type
        self.content = content


class SimpleInMemoryChatMessageHistory:
    def __init__(self):
        self.messages = []

    def add_user_message(self, content):
        self.messages.append(SimpleMessage("human", content))

    def add_ai_message(self, content):
        self.messages.append(SimpleMessage("ai", content))

    def clear(self):
        self.messages.clear()


_store = OrderedDict()


def get_session_history(session_id):
    if session_id in _store:
        _store.move_to_end(session_id)  # LRU 갱신
    else:
        if InMemoryChatMessageHistory is not None:
            _store[session_id] = InMemoryChatMessageHistory()
        else:
            _store[session_id] = SimpleInMemoryChatMessageHistory()
        while len(_store) > MAX_SESSIONS:
            _store.popitem(last=False)  # 가장 오래 사용되지 않은 세션 제거

    history = _store[session_id]
    if len(history.messages) > MAX_MESSAGES_PER_SESSION:
        del history.messages[:-MAX_MESSAGES_PER_SESSION]
    return history


def serialize_history(session_id, limit=10):
    history = get_session_history(session_id)
    messages = history.messages[-limit:]

    return [
        {
            "role": "user" if message.type in ("human", "user") else "assistant",
            "content": message.content,
        }
        for message in messages
    ]
