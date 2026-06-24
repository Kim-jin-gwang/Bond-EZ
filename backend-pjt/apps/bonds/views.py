from django.views.decorators.http import require_GET

from apps.accounts.services import record_search_log
from apps.common.responses import error, ok, paginated_response

from .models import BondType, CreditRating, GuaranteeStatus, Industry, Seniority
from .selectors import filtered_bonds, get_bond, get_bonds_for_compare, get_latest_market_data, market_data_history, get_curated_bonds
from .serializers import (
    serialize_bond_compare_item,
    serialize_bond_detail,
    serialize_bond_list_item,
    serialize_cashflow_rule,
    serialize_market_data,
)


@require_GET
def bond_list(request):
    if not request.session.session_key:
        request.session.create()
    record_search_log(request.user, request.session.session_key, request.GET)
    return paginated_response(filtered_bonds(request.GET), request, serialize_bond_list_item)


@require_GET
def bond_curated(request):
    if not request.session.session_key:
        request.session.create()
    limit_val = request.GET.get("limit")
    limit = int(limit_val) if (limit_val and limit_val.isdigit()) else 10
    curated = get_curated_bonds(request.user, request.session.session_key, limit=limit)
    return ok({"items": [serialize_bond_list_item(bond) for bond in curated]})




@require_GET
def bond_detail(request, bond_id):
    bond = get_bond(bond_id)
    if bond is None:
        return error("BOND_NOT_FOUND", "채권 정보를 찾을 수 없습니다.", status=404)
    return ok(serialize_bond_detail(bond))


@require_GET
def bond_compare(request):
    raw_ids = request.GET.get("ids", "")
    if not raw_ids:
        return error(
            "REQUIRED_QUERY_PARAMETER_MISSING",
            "ids는 필수입니다.",
            details={"field": "ids"},
        )

    try:
        bond_ids = [int(raw_id) for raw_id in raw_ids.split(",") if raw_id.strip()]
    except ValueError:
        return error(
            "INVALID_QUERY_PARAMETER",
            "ids는 쉼표로 구분된 숫자 형식이어야 합니다.",
            details={"field": "ids"},
        )

    bond_ids = list(dict.fromkeys(bond_ids))
    if len(bond_ids) != 2:
        return error(
            "COMPARE_BONDS_COUNT_INVALID",
            "비교할 채권은 정확히 2개여야 합니다.",
            details={"field": "ids", "required_count": 2},
        )

    bonds = get_bonds_for_compare(bond_ids)
    found_ids = {bond.id for bond in bonds}
    missing_ids = [bond_id for bond_id in bond_ids if bond_id not in found_ids]
    if missing_ids:
        return error(
            "BOND_NOT_FOUND",
            "비교 대상 채권 중 찾을 수 없는 채권이 있습니다.",
            status=404,
            details={"missing_ids": missing_ids},
        )

    return ok(
        {
            "items": [serialize_bond_compare_item(bond) for bond in bonds],
            "comparison_fields": [
                "issuer_name",
                "industry_name",
                "bond_type",
                "credit_rating",
                "coupon_rate",
                "maturity_date",
                "ytm",
                "duration",
                "price",
                "trading_volume",
                "option_type",
                "next_exercise_date",
                "guarantee_status",
                "seniority",
            ],
        }
    )


@require_GET
def bond_cashflows(request, bond_id):
    bond = get_bond(bond_id)
    if bond is None:
        return error("BOND_NOT_FOUND", "채권 정보를 찾을 수 없습니다.", status=404)
    return ok(serialize_cashflow_rule(bond))


@require_GET
def bond_market_data_history(request, bond_id):
    if get_bond(bond_id) is None:
        return error("BOND_NOT_FOUND", "채권 정보를 찾을 수 없습니다.", status=404)

    return ok(
        {
            "bond_id": bond_id,
            "items": [serialize_market_data(item) for item in market_data_history(bond_id, request.GET)],
        }
    )


@require_GET
def bond_latest_market_data(request, bond_id):
    market_data = get_latest_market_data(bond_id)
    if market_data is None:
        return error(
            "BOND_MARKET_DATA_NOT_FOUND",
            "채권의 최신 시장 데이터를 찾을 수 없습니다.",
            status=404,
        )
    return ok({"bond_id": bond_id, "market_data": serialize_market_data(market_data)})


@require_GET
def bond_filter_options(request):
    return ok(
        {
            "bond_types": list(
                BondType.objects.filter(deleted_at__isnull=True).values("id", "bond_type").order_by("bond_type")
            ),
            "credit_ratings": list(
                CreditRating.objects.filter(deleted_at__isnull=True)
                .values("id", "rating_name", "rating_order")
                .order_by("rating_order", "rating_name")
            ),
            "industries": list(
                Industry.objects.filter(deleted_at__isnull=True)
                .values("id", "industry_name")
                .order_by("industry_name")
            ),
            "seniorities": list(
                Seniority.objects.filter(deleted_at__isnull=True)
                .values("id", "seniority_name")
                .order_by("seniority_name")
            ),
            "guarantee_statuses": list(
                GuaranteeStatus.objects.filter(deleted_at__isnull=True)
                .values("id", "guarantee_status")
                .order_by("guarantee_status")
            ),
        }
    )
