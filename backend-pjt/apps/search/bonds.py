from datetime import date
from math import ceil

from django.conf import settings

from apps.bonds.selectors import filtered_bonds
from apps.bonds.serializers import serialize_bond_list_item

from .clients import get_elasticsearch_client

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

MATURITY_RANGES = {
    "1년 이하": {"lt": 1},
    "1~3년": {"gte": 1, "lt": 3},
    "3~5년": {"gte": 3, "lt": 5},
    "5~10년": {"gte": 5, "lt": 10},
    "10년 이상": {"gte": 10},
}

COUPON_THRESHOLDS = {
    "1% 이상": 1,
    "2% 이상": 2,
    "3% 이상": 3,
    "4% 이상": 4,
    "5% 이상": 5,
}

OPTION_ALIASES = {
    "없음": ["없음", "NONE", "옵션해당사항없음", "옵션해당 사항 없음"],
    "옵션해당사항없음": ["없음", "NONE", "옵션해당사항없음", "옵션해당 사항 없음"],
    "옵션해당 사항 없음": ["없음", "NONE", "옵션해당사항없음", "옵션해당 사항 없음"],
    "NONE": ["없음", "NONE", "옵션해당사항없음", "옵션해당 사항 없음"],
    "CALL": ["CALL", "CALL+PUT"],
    "PUT": ["PUT", "CALL+PUT"],
}


class SearchUnavailable(Exception):
    pass


def search_bonds(params):
    page = positive_int(params.get("page"), 1)
    size = min(positive_int(params.get("size"), DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE)
    client = get_elasticsearch_client()

    if client is None:
        raise SearchUnavailable("Elasticsearch client is not installed.")

    body = build_bond_search_body(params, page, size)
    response = client.search(index=settings.ELASTICSEARCH_BONDS_INDEX, **body)
    total = response["hits"]["total"]
    total_value = total.get("value", 0) if isinstance(total, dict) else total

    return {
        "data": [normalize_bond_hit(hit["_source"]) for hit in response["hits"]["hits"]],
        "page": {
            "number": page,
            "size": size,
            "total_elements": total_value,
            "total_pages": ceil(total_value / size) if total_value else 0,
        },
    }


def fallback_search_bonds(params):
    fallback_params = params.copy()
    normalize_fallback_params(fallback_params)
    page = positive_int(params.get("page"), 1)
    size = min(positive_int(params.get("size"), DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE)
    queryset = filtered_bonds(fallback_params)
    total = queryset.count()
    start = (page - 1) * size
    end = start + size

    return {
        "data": [serialize_bond_list_item(bond) for bond in queryset[start:end]],
        "page": {
            "number": page,
            "size": size,
            "total_elements": total,
            "total_pages": ceil(total / size) if total else 0,
        },
        "search_engine": "database",
    }


def build_bond_search_body(params, page, size):
    must = []
    filters = []
    keyword = (params.get("keyword") or params.get("q") or "").strip()

    if keyword:
        must.append(
            {
                "bool": {
                    "should": [
                        {"term": {"isin_code": {"value": keyword, "boost": 6}}},
                        {"term": {"short_code": {"value": keyword, "boost": 5}}},
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": [
                                    "bond_name^4",
                                    "short_name^3",
                                    "issuer_name^2",
                                    "isin_code",
                                    "short_code",
                                ],
                                "type": "best_fields",
                                "operator": "and",
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            }
        )

    add_terms_filter(filters, "bond_type", values(params, "bond_type"))
    add_terms_filter(filters, "rating_group", values(params, "rating_group"))
    add_terms_filter(filters, "payment_cycle_months", number_values(params, "payment_cycle_months"))
    add_terms_filter(filters, "seniority", values(params, "seniority"))
    add_terms_filter(filters, "option_type", option_values(params))
    add_terms_filter(filters, "guarantee_status", values(params, "guarantee_status"))
    add_terms_filter(filters, "industry_id", number_values(params, "industry_id"))
    add_maturity_filter(filters, values(params, "maturity_bucket"))
    add_coupon_filter(filters, params)

    query = {"bool": {"filter": filters}}
    if must:
        query["bool"]["must"] = must
    else:
        query["bool"]["must"] = [{"match_all": {}}]

    return {
        "from_": (page - 1) * size,
        "size": size,
        "query": query,
        "sort": sort_clause(params.get("sort")),
        "track_total_hits": True,
    }


def normalize_bond_hit(source):
    return {
        "bond_id": source.get("bond_id"),
        "isin_code": source.get("isin_code"),
        "short_code": source.get("short_code"),
        "bond_name": source.get("bond_name"),
        "short_name": source.get("short_name"),
        "issuer": {
            "issuer_id": source.get("issuer_id"),
            "issuer_name": source.get("issuer_name"),
            "industry": {
                "industry_id": source.get("industry_id"),
                "industry_name": source.get("industry_name"),
            },
        },
        "bond_type": source.get("bond_type"),
        "credit_rating": source.get("rating_name"),
        "rating_group": source.get("rating_group"),
        "seniority": source.get("seniority"),
        "guarantee_status": source.get("guarantee_status"),
        "coupon_rate": source.get("coupon_rate"),
        "maturity_date": source.get("maturity_date"),
        "payment_cycle_months": source.get("payment_cycle_months"),
        "interest_type": source.get("interest_type"),
        "option_type": source.get("option_type"),
        "next_exercise_date": source.get("next_exercise_date"),
        "latest_market_data": {
            "market_data_id": source.get("market_data_id"),
            "base_date": source.get("market_base_date"),
            "price": source.get("price"),
            "ytm": source.get("ytm"),
            "trading_volume": source.get("trading_volume"),
            "bid_yield": source.get("bid_yield"),
            "ask_yield": source.get("ask_yield"),
            "price_change_rate": source.get("price_change_rate"),
        } if source.get("market_data_id") is not None else None,
    }


def add_terms_filter(filters, field, items):
    if items:
        filters.append({"terms": {field: items}})


def add_maturity_filter(filters, buckets):
    ranges = [MATURITY_RANGES[bucket] for bucket in buckets if bucket in MATURITY_RANGES]
    if ranges:
        filters.append(
            {
                "bool": {
                    "should": [{"range": {"maturity_years": range_value}} for range_value in ranges],
                    "minimum_should_match": 1,
                }
            }
        )


def add_coupon_filter(filters, params):
    thresholds = [COUPON_THRESHOLDS[item] for item in values(params, "coupon_bucket") if item in COUPON_THRESHOLDS]
    explicit_min = decimal_value(params.get("min_coupon"))
    minimum = min(thresholds) if thresholds else explicit_min

    range_filter = {}
    if minimum is not None:
        range_filter["gte"] = minimum

    explicit_max = decimal_value(params.get("max_coupon"))
    if explicit_max is not None:
        range_filter["lte"] = explicit_max

    if range_filter:
        filters.append({"range": {"coupon_rate": range_filter}})


def option_values(params):
    result = []
    for item in values(params, "option_type"):
        result.extend(OPTION_ALIASES.get(item, [item]))
    return list(dict.fromkeys(result))


def sort_clause(sort):
    sort_map = {
        "maturity_asc": [{"maturity_date": {"order": "asc", "missing": "_last"}}],
        "maturity_desc": [{"maturity_date": {"order": "desc", "missing": "_last"}}],
        "coupon_rate_desc": [{"coupon_rate": {"order": "desc", "missing": "_last"}}],
        "coupon_rate_asc": [{"coupon_rate": {"order": "asc", "missing": "_last"}}],
        "ytm_desc": [{"ytm": {"order": "desc", "missing": "_last"}}],
        "ytm_asc": [{"ytm": {"order": "asc", "missing": "_last"}}],
        "trading_volume_desc": [{"trading_volume": {"order": "desc", "missing": "_last"}}],
        "price_change_rate_desc": [{"price_change_rate": {"order": "desc", "missing": "_last"}}],
    }
    return [*sort_map.get(sort, [{"maturity_date": {"order": "asc", "missing": "_last"}}]), {"bond_id": "asc"}]


def values(params, key):
    raw = params.get(key)
    if not raw:
        return []
    if isinstance(raw, (list, tuple)):
        items = raw
    else:
        items = str(raw).split(",")
    return [item.strip() for item in items if str(item).strip()]


def number_values(params, key):
    result = []
    for item in values(params, key):
        number = positive_int(item, None)
        if number is not None:
            result.append(number)
    return result


def positive_int(value, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def decimal_value(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_fallback_params(params):
    for key in ("bond_type", "rating_group", "seniority", "guarantee_status"):
        items = values(params, key)
        if items:
            params[key] = items

    option_types = values(params, "option_type")
    if option_types:
        mapped_option_types = []
        for opt in option_types:
            if opt in ("없음", "NONE", "옵션해당사항없음", "옵션해당 사항 없음"):
                mapped_option_types.append("옵션해당사항없음")
            else:
                mapped_option_types.append(opt)
        params["option_type"] = mapped_option_types

    payment_cycles = values(params, "payment_cycle_months")
    if payment_cycles:
        params["payment_cycle_months"] = [int(x) for x in payment_cycles if x.isdigit()]

    industry_ids = values(params, "industry_id")
    if industry_ids:
        params["industry_id"] = [int(x) for x in industry_ids if x.isdigit()]

    coupon_buckets = values(params, "coupon_bucket")
    thresholds = [COUPON_THRESHOLDS[item] for item in coupon_buckets if item in COUPON_THRESHOLDS]
    if thresholds:
        params["min_coupon"] = min(thresholds)

    today = date.today()
    maturity_buckets = values(params, "maturity_bucket")
    if len(maturity_buckets) == 1 and maturity_buckets[0] in MATURITY_RANGES:
        selected = MATURITY_RANGES[maturity_buckets[0]]
        if "gte" in selected:
            params["maturity_from"] = date(today.year + int(selected["gte"]), today.month, today.day).isoformat()
        if "lt" in selected:
            params["maturity_to"] = date(today.year + int(selected["lt"]), today.month, today.day).isoformat()
