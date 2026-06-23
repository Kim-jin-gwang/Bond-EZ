from django.db.models import OuterRef, Q, Subquery

from .models import Bond, BondMarketData, BondsMaster


def has_normal_bonds():
    return Bond.objects.filter(deleted_at__isnull=True).exists()


def base_bond_queryset():
    latest_market_data = BondMarketData.objects.filter(
        bond_id=OuterRef("pk"),
        deleted_at__isnull=True,
    ).order_by("-base_date")

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
        .annotate(
            latest_market_data_id=Subquery(latest_market_data.values("id")[:1]),
            latest_market_data_base_date=Subquery(latest_market_data.values("base_date")[:1]),
            latest_market_data_price=Subquery(latest_market_data.values("price")[:1]),
            latest_market_data_substitute_price=Subquery(latest_market_data.values("substitute_price")[:1]),
            latest_market_data_ytm=Subquery(latest_market_data.values("ytm")[:1]),
            latest_market_data_duration=Subquery(latest_market_data.values("duration")[:1]),
            latest_market_data_spread=Subquery(latest_market_data.values("spread")[:1]),
            latest_market_data_trading_volume=Subquery(latest_market_data.values("trading_volume")[:1]),
            latest_market_data_bid_yield=Subquery(latest_market_data.values("bid_yield")[:1]),
            latest_market_data_ask_yield=Subquery(latest_market_data.values("ask_yield")[:1]),
            latest_market_data_price_change_rate=Subquery(latest_market_data.values("price_change_rate")[:1]),
        )
    )


def filtered_bonds(params):
    if not has_normal_bonds():
        queryset = BondsMaster.objects.all()
        keyword = params.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(bond_name__icontains=keyword)
                | Q(isin_code__icontains=keyword)
                | Q(company_name__icontains=keyword)
            )

        bond_type = params.get("bond_type")
        if bond_type:
            queryset = queryset.filter(bond_type=bond_type)

        rating_group = params.get("rating_group")
        if rating_group:
            queryset = queryset.filter(credit_rating__startswith=rating_group)

        maturity_from = params.get("maturity_from")
        if maturity_from:
            queryset = queryset.filter(maturity_date__gte=maturity_from)

        maturity_to = params.get("maturity_to")
        if maturity_to:
            queryset = queryset.filter(maturity_date__lte=maturity_to)

        ordering_map = {
            "maturity_asc": "maturity_date",
            "maturity_desc": "-maturity_date",
            "coupon_rate_desc": "-coupon_rate",
            "coupon_rate_asc": "coupon_rate",
        }
        ordering = ordering_map.get(params.get("sort"), "maturity_date")
        return queryset.order_by(ordering, "isin_code")

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
        queryset = queryset.filter(latest_market_data_ytm__gte=min_ytm)

    max_ytm = params.get("max_ytm")
    if max_ytm:
        queryset = queryset.filter(latest_market_data_ytm__lte=max_ytm)

    ordering_map = {
        "maturity_asc": "maturity_date",
        "maturity_desc": "-maturity_date",
        "coupon_rate_desc": "-coupon_rate",
        "coupon_rate_asc": "coupon_rate",
        "ytm_desc": "-latest_market_data_ytm",
        "ytm_asc": "latest_market_data_ytm",
        "trading_volume_desc": "-latest_market_data_trading_volume",
        "price_change_rate_desc": "-latest_market_data_price_change_rate",
    }
    ordering = ordering_map.get(params.get("sort"), "maturity_date")
    return queryset.order_by(ordering, "id")


def get_bond(bond_id):
    bond = None
    if str(bond_id).isdigit():
        bond = base_bond_queryset().filter(id=bond_id).first()
    if bond is not None:
        return bond
    return BondsMaster.objects.filter(isin_code=bond_id).first()


def get_bonds_for_compare(bond_ids):
    if not has_normal_bonds():
        bonds = BondsMaster.objects.filter(isin_code__in=bond_ids)
        bonds_by_id = {bond.isin_code: bond for bond in bonds}
        return [bonds_by_id[bond_id] for bond_id in bond_ids if bond_id in bonds_by_id]

    numeric_ids = [bond_id for bond_id in bond_ids if str(bond_id).isdigit()]
    bonds = base_bond_queryset().filter(id__in=numeric_ids)
    bonds_by_id = {str(bond.id): bond for bond in bonds}
    return [bonds_by_id[str(bond_id)] for bond_id in bond_ids if str(bond_id) in bonds_by_id]


def get_latest_market_data(bond_id):
    if not str(bond_id).isdigit():
        return None
    return (
        BondMarketData.objects.filter(bond_id=bond_id, deleted_at__isnull=True)
        .order_by("-base_date")
        .first()
    )


def market_data_history(bond_id, params):
    if not str(bond_id).isdigit():
        return BondMarketData.objects.none()

    queryset = BondMarketData.objects.filter(bond_id=bond_id, deleted_at__isnull=True)
    date_from = params.get("from") or params.get("start_date")
    date_to = params.get("to") or params.get("end_date")

    if date_from:
        queryset = queryset.filter(base_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(base_date__lte=date_to)

    return queryset.order_by("base_date")
