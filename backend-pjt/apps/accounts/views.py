from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.common.responses import error, ok, parse_json_body

from .serializers import serialize_user
from .services import create_user, login_user, logout_user, update_user


def require_authenticated_user(request):
    if request.user.is_authenticated:
        return None
    return error("UNAUTHORIZED", "로그인이 필요합니다.", status=401)


@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    body = parse_json_body(request)
    if body is None:
        return error("INVALID_JSON_BODY", "요청 본문이 올바른 JSON 형식이 아닙니다.")

    user, service_error = create_user(body)
    if service_error:
        error_code, message, details = service_error
        return error(error_code, message, details=details)

    return ok({"user": serialize_user(user)}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    body = parse_json_body(request)
    if body is None:
        return error("INVALID_JSON_BODY", "요청 본문이 올바른 JSON 형식이 아닙니다.")

    user, service_error = login_user(request, body)
    if service_error:
        error_code, message, details = service_error
        return error(error_code, message, status=401, details=details)

    return ok({"user": serialize_user(user)})


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    logout_user(request)
    return ok({}, status=204)


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def me(request):
    auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    if request.method == "GET":
        return ok({"user": serialize_user(request.user)})

    body = parse_json_body(request)
    if body is None:
        return error("INVALID_JSON_BODY", "요청 본문이 올바른 JSON 형식이 아닙니다.")

    service_error = update_user(request.user, body)
    if service_error:
        error_code, message, details = service_error
        return error(error_code, message, details=details)

    return ok({"user": serialize_user(request.user)})
