try:
    from langchain_core.chat_history import InMemoryChatMessageHistory
except ImportError:
    InMemoryChatMessageHistory = None


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


_store = {}


def get_session_history(session_id):
    if session_id not in _store:
        if InMemoryChatMessageHistory is not None:
            _store[session_id] = InMemoryChatMessageHistory()
        else:
            _store[session_id] = SimpleInMemoryChatMessageHistory()
    return _store[session_id]


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

