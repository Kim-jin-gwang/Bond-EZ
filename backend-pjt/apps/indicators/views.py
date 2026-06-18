from django.views.decorators.http import require_GET

from apps.bonds.serializers import number_or_none
from apps.common.responses import ok, paginated_response

from .selectors import credit_rating_rates, latest_base_rates, latest_deposit_rates
from .serializers import serialize_base_rate, serialize_credit_rating_rate, serialize_deposit_rate


@require_GET
def indicator_summary(request):
    return ok(
        {
            "items": [
                {
                    "id": "treasury-rate",
                    "title": "국고채 / 미국채 금리",
                    "endpoint": "/api/v1/base-rates/treasury-rates",
                },
                {
                    "id": "central-bank-rate",
                    "title": "나라별 기준 금리",
                    "endpoint": "/api/v1/base-rates",
                },
                {
                    "id": "credit-rating-yield",
                    "title": "신용등급별 평균 금리",
                    "endpoint": "/api/v1/credit-ratings/rates",
                },
                {
                    "id": "deposit-compare",
                    "title": "예금 금리 비교",
                    "endpoint": "/api/v1/deposit-rates",
                },
                {
                    "id": "yield-spread",
                    "title": "장단기 금리차",
                    "endpoint": "/api/v1/base-rates/yield-spreads",
                },
                {
                    "id": "yield-curve",
                    "title": "Yield Curve",
                    "endpoint": "/api/v1/base-rates/yield-curve",
                },
            ]
        }
    )


@require_GET
def base_rate_list(request):
    return ok({"items": [serialize_base_rate(item) for item in latest_base_rates()]})


@require_GET
def treasury_rates(request):
    items = [
        {
            "country": item.country.country_name,
            "three_year_yield": number_or_none(item.three_year_yield),
            "ten_year_yield": number_or_none(item.ten_year_yield),
        }
        for item in latest_base_rates()
    ]
    return ok({"items": items})


@require_GET
def yield_spreads(request):
    items = [
        {
            "country": item.country.country_name,
            "yield_curve_spread": number_or_none(item.yield_curve_spread),
        }
        for item in latest_base_rates()
    ]
    return ok({"items": items})


@require_GET
def yield_curve(request):
    items = [
        {
            "country": item.country.country_name,
            "points": [
                {"maturity": "3Y", "yield": number_or_none(item.three_year_yield)},
                {"maturity": "10Y", "yield": number_or_none(item.ten_year_yield)},
            ],
        }
        for item in latest_base_rates()
    ]
    return ok({"items": items})


@require_GET
def deposit_rate_list(request):
    return paginated_response(latest_deposit_rates(), request, serialize_deposit_rate)


@require_GET
def credit_rating_rate_list(request):
    return ok({"items": [serialize_credit_rating_rate(row) for row in credit_rating_rates()]})
