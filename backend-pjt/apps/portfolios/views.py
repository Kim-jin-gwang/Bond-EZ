from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.common.responses import error, ok, parse_json_body

from .selectors import get_active_bond_for_portfolio, get_user_bond, user_bonds_for
from .serializers import serialize_user_bond
from .services import create_or_update_user_bond, delete_user_bond


def require_authenticated_user(request):
    if request.user.is_authenticated:
        return None
    return error("UNAUTHORIZED", "로그인이 필요합니다.", status=401)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def my_bonds(request):
    auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    if request.method == "GET":
        return ok({"items": [serialize_user_bond(item) for item in user_bonds_for(request.user)]})

    body = parse_json_body(request)
    if body is None:
        return error("INVALID_JSON_BODY", "요청 본문이 올바른 JSON 형식이 아닙니다.")

    bond_id = body.get("bond_id")
    if not bond_id:
        return error("REQUIRED_FIELD_MISSING", "bond_id는 필수입니다.", details={"field": "bond_id"})

    bond = get_active_bond_for_portfolio(bond_id)
    if bond is None:
        return error("BOND_NOT_FOUND", "채권 정보를 찾을 수 없습니다.", status=404)

    user_bond = create_or_update_user_bond(request.user, bond, body)
    return ok(serialize_user_bond(user_bond), status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def my_bond_delete(request, user_bond_id):
    auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    user_bond = get_user_bond(request.user, user_bond_id)
    if user_bond is None:
        return error("USER_BOND_NOT_FOUND", "보유 채권 정보를 찾을 수 없습니다.", status=404)

    delete_user_bond(user_bond)
    return ok({}, status=204)

