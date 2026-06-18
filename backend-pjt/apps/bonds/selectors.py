from django.db.models import OuterRef, Prefetch, Q, Subquery

from .models import Bond, BondMarketData


def base_bond_queryset():
    latest_market_data_ids = (
        BondMarketData.objects.filter(bond_id=OuterRef("pk"), deleted_at__isnull=True)
        .order_by("-base_date")
        .values("id")[:1]
    )
    latest_market_data = BondMarketData.objects.filter(
        id__in=Subquery(latest_market_data_ids),
        deleted_at__isnull=True,
    )

    return (
        Bond.objects.filter(deleted_at__isnull=True)
        .select_related(
            "issuer",
            "issuer__industry",
            "bond_type",
            "rating",
            "seniority",
            "guarantee_status",
            "cashflow_rule",
            "option_exercise",
        )
        .prefetch_related(
            Prefetch("market_data", queryset=latest_market_data, to_attr="prefetched_latest_market_data")
        )
    )


def filtered_bonds(params):
    queryset = base_bond_queryset()

    keyword = params.get("keyword")
    if keyword:
        queryset = queryset.filter(
            Q(bond_name__icontains=keyword)
            | Q(short_name__icontains=keyword)
            | Q(isin_code__icontains=keyword)
            | Q(short_code__icontains=keyword)
            | Q(issuer__issuer_name__icontains=keyword)
        )

    filter_map = {
        "bond_type": "bond_type__bond_type",
        "credit_rating": "rating__rating_name",
        "issuer_id": "issuer_id",
        "industry_id": "issuer__industry_id",
        "seniority": "seniority__seniority_name",
        "guarantee_status": "guarantee_status__guarantee_status",
        "option_type": "option_exercise__option_type",
        "interest_type": "interest_type",
        "payment_cycle_months": "cashflow_rule__interest_payment_unit_months",
    }
    for param, lookup in filter_map.items():
        value = params.get(param)
        if value:
            queryset = queryset.filter(**{lookup: value})

    rating_group = params.get("rating_group")
    if rating_group:
        queryset = queryset.filter(rating__rating_name__startswith=rating_group)

    maturity_from = params.get("maturity_from")
    if maturity_from:
        queryset = queryset.filter(maturity_date__gte=maturity_from)

    maturity_to = params.get("maturity_to")
    if maturity_to:
        queryset = queryset.filter(maturity_date__lte=maturity_to)

    min_ytm = params.get("min_ytm")
    if min_ytm:
        queryset = queryset.filter(market_data__ytm__gte=min_ytm)

    max_ytm = params.get("max_ytm")
    if max_ytm:
        queryset = queryset.filter(market_data__ytm__lte=max_ytm)

    ordering_map = {
        "maturity_asc": "maturity_date",
        "maturity_desc": "-maturity_date",
        "coupon_rate_desc": "-coupon_rate",
        "coupon_rate_asc": "coupon_rate",
        "ytm_desc": "-market_data__ytm",
        "ytm_asc": "market_data__ytm",
        "trading_volume_desc": "-market_data__trading_volume",
        "price_change_rate_desc": "-market_data__price_change_rate",
    }
    ordering = ordering_map.get(params.get("sort"), "maturity_date")
    return queryset.order_by(ordering, "id").distinct()


def get_bond(bond_id):
    return base_bond_queryset().filter(id=bond_id).first()


def get_latest_market_data(bond_id):
    return (
        BondMarketData.objects.filter(bond_id=bond_id, deleted_at__isnull=True)
        .order_by("-base_date")
        .first()
    )


def market_data_history(bond_id, params):
    queryset = BondMarketData.objects.filter(bond_id=bond_id, deleted_at__isnull=True)
    date_from = params.get("from") or params.get("start_date")
    date_to = params.get("to") or params.get("end_date")

    if date_from:
        queryset = queryset.filter(base_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(base_date__lte=date_to)

    return queryset.order_by("base_date")
