from apps.bonds.serializers import number_or_none


def serialize_base_rate(base_rate):
    return {
        "base_rate_id": base_rate.id,
        "country": {
            "country_id": base_rate.country_id,
            "country_name": base_rate.country.country_name,
        },
        "base_interest_rate": number_or_none(base_rate.base_interest_rate),
        "three_year_yield": number_or_none(base_rate.three_year_yield),
        "ten_year_yield": number_or_none(base_rate.ten_year_yield),
        "yield_curve_spread": number_or_none(base_rate.yield_curve_spread),
        "created_at": base_rate.created_at.isoformat() if base_rate.created_at else None,
    }


def serialize_deposit_rate(deposit_rate):
    return {
        "deposit_rate_id": deposit_rate.id,
        "bank": {
            "bank_id": deposit_rate.bank_id,
            "bank_name": deposit_rate.bank.bank_name,
        },
        "product_name": deposit_rate.product_name,
        "base_rate": number_or_none(deposit_rate.base_rate),
        "prime_rate": number_or_none(deposit_rate.prime_rate),
        "created_at": deposit_rate.created_at.isoformat() if deposit_rate.created_at else None,
    }


def serialize_credit_rating_rate(row):
    rating_name = row.get("rating__rating_name") or row["bond__rating__rating_name"]
    return {
        "credit_rating": rating_name,
        "rating_group": rating_name.rstrip("+-0123456789"),
        "average_ytm": number_or_none(row["average_ytm"]),
        "bond_count": row["bond_count"],
    }
