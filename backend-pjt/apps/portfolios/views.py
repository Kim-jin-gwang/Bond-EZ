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


@csrf_exempt
@require_http_methods(["GET", "POST"])
def my_favorites(request):
    auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    if request.method == "GET":
        from .models import FavoriteBond
        from apps.bonds.serializers import serialize_bond_list_item
        from apps.bonds.selectors import base_bond_queryset
        bond_ids = FavoriteBond.objects.filter(user=request.user).values_list("bond_id", flat=True)
        bonds = base_bond_queryset().filter(id__in=bond_ids)
        return ok({"items": [serialize_bond_list_item(bond) for bond in bonds]})

    body = parse_json_body(request)
    if body is None:
        return error("INVALID_JSON_BODY", "요청 본문이 올바른 JSON 형식이 아닙니다.")

    bond_id = body.get("bond_id")
    if not bond_id:
        return error("REQUIRED_FIELD_MISSING", "bond_id는 필수입니다.", details={"field": "bond_id"})

    from apps.portfolios.selectors import get_active_bond_for_portfolio
    bond = get_active_bond_for_portfolio(bond_id)
    if bond is None:
        return error("BOND_NOT_FOUND", "채권 정보를 찾을 수 없습니다.", status=404)

    from .models import FavoriteBond
    from apps.bonds.serializers import serialize_bond_list_item
    favorite_bond, created = FavoriteBond.objects.get_or_create(user=request.user, bond=bond)
    
    from apps.bonds.selectors import base_bond_queryset
    serialized_bond = base_bond_queryset().filter(id=bond.id).first()
    return ok(serialize_bond_list_item(serialized_bond or bond), status=201 if created else 200)


@csrf_exempt
@require_http_methods(["DELETE"])
def my_favorite_delete(request, bond_id):
    auth_error = require_authenticated_user(request)
    if auth_error:
        return auth_error

    from .models import FavoriteBond
    deleted, _ = FavoriteBond.objects.filter(user=request.user, bond_id=bond_id).delete()
    if not deleted:
        return error("FAVORITE_BOND_NOT_FOUND", "관심 채권 정보를 찾을 수 없습니다.", status=404)

    return ok({}, status=204)


