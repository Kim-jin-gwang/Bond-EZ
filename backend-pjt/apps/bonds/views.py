from django.views.decorators.http import require_GET

from apps.common.responses import error, ok, paginated_response

from .models import BondType, CreditRating, GuaranteeStatus, Industry, Seniority
from .selectors import filtered_bonds, get_bond, get_latest_market_data, market_data_history
from .serializers import (
    serialize_bond_detail,
    serialize_bond_list_item,
    serialize_cashflow_rule,
    serialize_market_data,
)


@require_GET
def bond_list(request):
    return paginated_response(filtered_bonds(request.GET), request, serialize_bond_list_item)


@require_GET
def bond_detail(request, bond_id):
    bond = get_bond(bond_id)
    if bond is None:
        return error("BOND_NOT_FOUND", "채권 정보를 찾을 수 없습니다.", status=404)
    return ok(serialize_bond_detail(bond))


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
