from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.common.responses import error, ok, parse_json_body

from .history import serialize_history
from .services import answer_chat


@csrf_exempt
@require_POST
def chat_message(request):
    payload = parse_json_body(request)
    if payload is None:
        return error("INVALID_JSON", "요청 본문은 JSON 형식이어야 합니다.")

    session_id = str(payload.get("session_id") or "").strip()
    message = str(payload.get("message") or "").strip()

    if not session_id:
        return error("CHAT_SESSION_ID_REQUIRED", "session_id가 필요합니다.", details={"field": "session_id"})

    if not message:
        return error("CHAT_MESSAGE_REQUIRED", "message가 필요합니다.", details={"field": "message"})

    result = answer_chat(session_id, message)
    return ok(
        {
            "session_id": session_id,
            "answer": result["answer"],
            "sources": result["sources"],
            "history": serialize_history(session_id),
        }
    )
