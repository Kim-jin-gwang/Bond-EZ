from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.common.responses import error, parse_json_body

from .services import answer_chat_stream


@csrf_exempt
@require_POST
def chat_message(request):
    payload = parse_json_body(request)
    if payload is None:
        return error("INVALID_JSON", "요청 본문은 JSON 형식이어야 합니다.")

    session_id = str(payload.get("session_id") or "").strip()
    message = str(payload.get("message") or "").strip()
    current_page = str(payload.get("current_page") or "").strip() or None
    page_params = payload.get("page_params") or {}

    if not session_id:
        return error("CHAT_SESSION_ID_REQUIRED", "session_id가 필요합니다.", details={"field": "session_id"})

    if not message:
        return error("CHAT_MESSAGE_REQUIRED", "message가 필요합니다.", details={"field": "message"})

    # SSE Event Generator
    def event_stream():
        for chunk in answer_chat_stream(session_id, message, current_page=current_page, page_params=page_params):
            yield chunk

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    # Disable caching & proxy buffering (critical for real-time SSE streaming)
    response["X-Accel-Buffering"] = "no"
    response["Cache-Control"] = "no-cache"
    return response

