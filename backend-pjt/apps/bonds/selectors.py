from django.core.cache import cache
from django.db.models import Q

from .models import Bond, BondMarketData, BondsMaster


def has_normal_bonds():
    cache_key = "bonds:has_normal_bonds"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    has_bonds = Bond.objects.filter(deleted_at__isnull=True).exists()
    cache.set(cache_key, has_bonds, timeout=60)
    return has_bonds


def base_bond_queryset():
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
            "latest_market_data",
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
            if isinstance(bond_type, str) and "," in bond_type:
                bond_type = [x.strip() for x in bond_type.split(",") if x.strip()]
            if isinstance(bond_type, (list, tuple)):
                queryset = queryset.filter(bond_type__in=bond_type)
            else:
                queryset = queryset.filter(bond_type=bond_type)

        rating_group = params.get("rating_group")
        if rating_group:
            if isinstance(rating_group, str) and "," in rating_group:
                rating_group = [x.strip() for x in rating_group.split(",") if x.strip()]
            if isinstance(rating_group, (list, tuple)):
                q_obj = Q()
                for rg in rating_group:
                    q_obj |= Q(credit_rating__startswith=rg)
                queryset = queryset.filter(q_obj)
            else:
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
        "payment_cycle_months": "payment_cycle_months",
    }
    for param, lookup in filter_map.items():
        value = params.get(param)
        if value:
            if isinstance(value, str):
                if "," in value:
                    value = [x.strip() for x in value.split(",") if x.strip()]
                elif value.strip():
                    value = value.strip()

            if isinstance(value, (list, tuple)):
                if param == "payment_cycle_months":
                    value = [int(x) for x in value if str(x).isdigit()]
                elif param == "industry_id":
                    value = [int(x) for x in value if str(x).isdigit()]
                elif param == "option_type":
                    mapped = []
                    for opt in value:
                        if opt in ("없음", "NONE", "옵션해당사항없음", "옵션해당 사항 없음"):
                            mapped.append("옵션해당사항없음")
                        else:
                            mapped.append(opt)
                    if "CALL" in mapped or "PUT" in mapped:
                        mapped.append("CALL+PUT")
                    value = list(set(mapped))

                if param == "option_type" and "옵션해당사항없음" in value:
                    queryset = queryset.filter(Q(option_exercise__option_type__in=value) | Q(option_exercise__isnull=True))
                else:
                    queryset = queryset.filter(**{f"{lookup}__in": value})
            else:
                if param == "payment_cycle_months" and str(value).isdigit():
                    value = int(value)
                elif param == "industry_id" and str(value).isdigit():
                    value = int(value)
                elif param == "option_type" and value in ("없음", "NONE", "옵션해당사항없음", "옵션해당 사항 없음"):
                    value = "옵션해당사항없음"

                if param == "option_type":
                    if value == "옵션해당사항없음":
                        queryset = queryset.filter(Q(option_exercise__option_type="옵션해당사항없음") | Q(option_exercise__isnull=True))
                    elif value in ("CALL", "PUT"):
                        queryset = queryset.filter(option_exercise__option_type__in=[value, "CALL+PUT"])
                    else:
                        queryset = queryset.filter(**{lookup: value})
                else:
                    queryset = queryset.filter(**{lookup: value})

    rating_group = params.get("rating_group")
    if rating_group:
        if isinstance(rating_group, str) and "," in rating_group:
            rating_group = [x.strip() for x in rating_group.split(",") if x.strip()]

        if isinstance(rating_group, (list, tuple)):
            q_obj = Q()
            for rg in rating_group:
                q_obj |= Q(rating__rating_name__startswith=rg)
            queryset = queryset.filter(q_obj)
        else:
            queryset = queryset.filter(rating__rating_name__startswith=rating_group)

    maturity_from = params.get("maturity_from")
    if maturity_from:
        queryset = queryset.filter(maturity_date__gte=maturity_from)

    maturity_to = params.get("maturity_to")
    if maturity_to:
        queryset = queryset.filter(maturity_date__lte=maturity_to)

    min_coupon = params.get("min_coupon")
    if min_coupon:
        try:
            min_val = float(min_coupon)
            queryset = queryset.filter(coupon_rate__gte=min_val)
        except (TypeError, ValueError):
            pass

    max_coupon = params.get("max_coupon")
    if max_coupon:
        try:
            max_val = float(max_coupon)
            queryset = queryset.filter(coupon_rate__lte=max_val)
        except (TypeError, ValueError):
            pass

    min_ytm = params.get("min_ytm")
    if min_ytm:
        queryset = queryset.filter(latest_market_data__ytm__gte=min_ytm)

    max_ytm = params.get("max_ytm")
    if max_ytm:
        queryset = queryset.filter(latest_market_data__ytm__lte=max_ytm)

    ordering_map = {
        "maturity_asc": "maturity_date",
        "maturity_desc": "-maturity_date",
        "coupon_rate_desc": "-coupon_rate",
        "coupon_rate_asc": "coupon_rate",
        "ytm_desc": "-latest_market_data__ytm",
        "ytm_asc": "latest_market_data__ytm",
        "trading_volume_desc": "-latest_market_data__trading_volume",
        "price_change_rate_desc": "-latest_market_data__price_change_rate",
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
