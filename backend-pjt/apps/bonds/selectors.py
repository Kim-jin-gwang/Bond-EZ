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

    has_price = params.get("has_price")
    if has_price in ("true", True, "True", 1, "1"):
        if has_normal_bonds():
            queryset = queryset.filter(latest_market_data__price__isnull=False)

    exclude_expired = params.get("exclude_expired")
    if exclude_expired in ("true", True, "True", 1, "1"):
        from django.utils import timezone
        today = timezone.now().date()
        queryset = queryset.filter(maturity_date__gte=today)

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


def get_curated_bonds(user, session_key, limit=10):
    from apps.accounts.models import UserSearchLog
    import collections

    # 1. Fetch search logs and favorite bonds
    logs = UserSearchLog.objects.none()
    favorites = []
    if user and user.is_authenticated:
        logs = UserSearchLog.objects.filter(user=user)
        from apps.portfolios.models import FavoriteBond
        favorites = list(FavoriteBond.objects.filter(user=user).select_related("bond"))
    elif session_key:
        logs = UserSearchLog.objects.filter(session_key=session_key)
        
    logs = logs.order_by("-created_at")[:20]  # Get last 20 search logs
    
    # 2. Build User Preference Profile
    keywords = []
    min_coupon_values = []
    max_coupon_values = []
    rating_groups = []
    bond_types = []
    
    # Process favorites first (give them high priority)
    for fav in favorites:
        bond = fav.bond
        bond_coupon = float(bond.coupon_rate) if bond.coupon_rate is not None else None
        if bond_coupon is not None:
            min_coupon_values.extend([bond_coupon, bond_coupon])
            
        bond_rating = bond.rating.rating_name if (hasattr(bond, 'rating') and bond.rating) else getattr(bond, 'credit_rating', '')
        if bond_rating:
            rating_groups.extend([bond_rating, bond_rating])
            
        bond_type_name = bond.bond_type.bond_type if (hasattr(bond, 'bond_type') and bond.bond_type) else getattr(bond, 'bond_type', '')
        if bond_type_name:
            bond_types.extend([bond_type_name, bond_type_name])
            
        if bond.bond_name:
            keywords.append(bond.bond_name.lower())

    for log in logs:
        if log.keyword:
            keywords.append(log.keyword.lower())
        filters = log.filters or {}
        
        # coupon rate
        if "min_coupon" in filters:
            try:
                min_coupon_values.append(float(filters["min_coupon"]))
            except (ValueError, TypeError):
                pass
        if "max_coupon" in filters:
            try:
                max_coupon_values.append(float(filters["max_coupon"]))
            except (ValueError, TypeError):
                pass
                
        # ratings
        if "rating_group" in filters:
            rg = filters["rating_group"]
            if isinstance(rg, list):
                rating_groups.extend(rg)
            else:
                rating_groups.append(rg)
        elif "credit_rating" in filters:
            cr = filters["credit_rating"]
            if isinstance(cr, list):
                rating_groups.extend(cr)
            else:
                rating_groups.append(cr)
                
        # bond type
        if "bond_type" in filters:
            bt = filters["bond_type"]
            if isinstance(bt, list):
                bond_types.extend(bt)
            else:
                bond_types.append(bt)

    # Calculate Profile Averages/Modes
    pref_coupon = None
    if min_coupon_values:
        pref_coupon = sum(min_coupon_values) / len(min_coupon_values)
    elif max_coupon_values:
        pref_coupon = sum(max_coupon_values) / len(max_coupon_values)
        
    # Count frequencies
    rating_counter = collections.Counter(rating_groups)
    bond_type_counter = collections.Counter(bond_types)
    
    total_ratings = sum(rating_counter.values()) or 1
    total_bond_types = sum(bond_type_counter.values()) or 1
    
    # Standard Fallback: if no logs and no favorites exist
    if not logs.exists() and not favorites:
        if not has_normal_bonds():
            queryset = BondsMaster.objects.all().order_by("-credit_rating", "-coupon_rate")
        else:
            queryset = base_bond_queryset().order_by("rating__rating_order", "-coupon_rate")
        if limit:
            queryset = queryset[:limit]
        return list(queryset)


    # Get active bonds
    has_normal = has_normal_bonds()
    if not has_normal:
        bond_values = list(BondsMaster.objects.all().values(
            "id", "isin_code", "bond_name", "company_name", "credit_rating", "coupon_rate", "bond_type"
        ))
    else:
        bond_values = list(
            Bond.objects.filter(deleted_at__isnull=True).values(
                "id",
                "isin_code",
                "bond_name",
                "coupon_rate",
                "issuer__issuer_name",
                "bond_type__bond_type",
                "rating__rating_name",
                "rating__rating_order",
            )
        )

    scored_bonds = []
    for bv in bond_values:
        score = 0.0
        
        # 1. Coupon Matching (30 points max)
        coupon_val = bv.get("coupon_rate")
        bond_coupon = float(coupon_val) if coupon_val is not None else 0.0
        if pref_coupon is not None:
            diff = abs(bond_coupon - pref_coupon)
            if bond_coupon >= pref_coupon:
                score += min(30, 25 + (bond_coupon - pref_coupon) * 2)
            else:
                score += max(0, 30 - diff * 8)
        else:
            score += min(30, bond_coupon * 5)

        # 2. Credit Rating Matching (30 points max)
        if has_normal:
            bond_rating = bv.get("rating__rating_name") or ""
        else:
            bond_rating = bv.get("credit_rating") or ""
            
        rating_score = 0.0
        for rg, count in rating_counter.items():
            weight = count / total_ratings
            if bond_rating.startswith(rg) or rg.startswith(bond_rating):
                rating_score += 30.0 * weight
                
        if total_ratings == 1 and not rating_groups:
            if has_normal:
                rating_order = bv.get("rating__rating_order")
                rating_order = rating_order if rating_order is not None else 10
            else:
                rating_order = 10
            rating_score = max(0, 30 - rating_order * 2)
        score += rating_score

        # 3. Bond Type Matching (20 points max)
        if has_normal:
            bond_type_name = bv.get("bond_type__bond_type") or ""
        else:
            bond_type_name = bv.get("bond_type") or ""
            
        bond_type_score = 0.0
        for bt, count in bond_type_counter.items():
            weight = count / total_bond_types
            if bond_type_name == bt:
                bond_type_score += 20.0 * weight
        if total_bond_types == 1 and not bond_types:
            bond_type_score = 15.0
        score += bond_type_score

        # 4. Keyword Relevancy (20 points max)
        keyword_score = 0.0
        if keywords:
            bond_name_val = bv.get("bond_name")
            bond_name_lower = bond_name_val.lower() if bond_name_val else ""
            if has_normal:
                issuer_name_val = bv.get("issuer__issuer_name")
                issuer_name_lower = issuer_name_val.lower() if issuer_name_val else ""
            else:
                issuer_name_val = bv.get("company_name")
                issuer_name_lower = issuer_name_val.lower() if issuer_name_val else ""
                
            for kw in keywords:
                if kw in bond_name_lower or kw in issuer_name_lower:
                    keyword_score = 20.0
                    break
        score += keyword_score

        key_val = bv.get("id") if has_normal else bv.get("isin_code")
        scored_bonds.append((key_val, score, bond_coupon))

    # Sort by score desc, then by coupon desc
    scored_bonds.sort(key=lambda x: (-x[1], -x[2]))
    
    if limit:
        top_keys = [sb[0] for sb in scored_bonds[:limit]]
    else:
        top_keys = [sb[0] for sb in scored_bonds]

    if not has_normal:
        full_bonds = BondsMaster.objects.filter(isin_code__in=top_keys)
        bond_map = {b.isin_code: b for b in full_bonds}
        return [bond_map[k] for k in top_keys if k in bond_map]
    else:
        full_bonds = base_bond_queryset().filter(id__in=top_keys)
        bond_map = {b.id: b for b in full_bonds}
        return [bond_map[k] for k in top_keys if k in bond_map]

