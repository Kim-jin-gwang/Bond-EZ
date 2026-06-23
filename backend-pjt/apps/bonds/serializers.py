def number_or_none(value):
    if value is None or value == "":
        return None

    if isinstance(value, str):
        normalized = "".join(ch for ch in value if ch.isdigit() or ch in ".-")
        if normalized in {"", ".", "-", "-."}:
            return None
        value = normalized

    return float(value)


def date_or_none(value):
    return None if value is None else value.isoformat()


def is_master_bond(bond):
    return hasattr(bond, "company_name") and hasattr(bond, "call_put_option")


def rating_group(value):
    return (value or "").rstrip("+-0123456789") or value


def payment_cycle_months(value):
    if value is None:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else None


def serialize_market_data(market_data):
    if market_data is None:
        return None

    if isinstance(market_data, dict):
        return {
            "market_data_id": market_data.get("id"),
            "base_date": date_or_none(market_data.get("base_date")),
            "price": number_or_none(market_data.get("price")),
            "substitute_price": market_data.get("substitute_price"),
            "ytm": number_or_none(market_data.get("ytm")),
            "duration": number_or_none(market_data.get("duration")),
            "spread": number_or_none(market_data.get("spread")),
            "trading_volume": market_data.get("trading_volume"),
            "bid_yield": number_or_none(market_data.get("bid_yield")),
            "ask_yield": number_or_none(market_data.get("ask_yield")),
            "price_change_rate": number_or_none(market_data.get("price_change_rate")),
        }

    return {
        "market_data_id": market_data.id,
        "base_date": date_or_none(market_data.base_date),
        "price": number_or_none(market_data.price),
        "substitute_price": market_data.substitute_price,
        "ytm": number_or_none(market_data.ytm),
        "duration": number_or_none(market_data.duration),
        "spread": number_or_none(market_data.spread),
        "trading_volume": market_data.trading_volume,
        "bid_yield": number_or_none(market_data.bid_yield),
        "ask_yield": number_or_none(market_data.ask_yield),
        "price_change_rate": number_or_none(market_data.price_change_rate),
    }


def serialize_list_market_data(market_data):
    if market_data is None:
        return None

    if isinstance(market_data, dict):
        return {
            "market_data_id": market_data.get("id"),
            "base_date": date_or_none(market_data.get("base_date")),
            "price": number_or_none(market_data.get("price")),
            "ytm": number_or_none(market_data.get("ytm")),
            "trading_volume": market_data.get("trading_volume"),
            "bid_yield": number_or_none(market_data.get("bid_yield")),
            "ask_yield": number_or_none(market_data.get("ask_yield")),
            "price_change_rate": number_or_none(market_data.get("price_change_rate")),
        }

    return {
        "market_data_id": market_data.id,
        "base_date": date_or_none(market_data.base_date),
        "price": number_or_none(market_data.price),
        "ytm": number_or_none(market_data.ytm),
        "trading_volume": market_data.trading_volume,
        "bid_yield": number_or_none(market_data.bid_yield),
        "ask_yield": number_or_none(market_data.ask_yield),
        "price_change_rate": number_or_none(market_data.price_change_rate),
    }


def get_latest_market_data(bond):
    annotated_id = getattr(bond, "latest_market_data_id", None)
    if annotated_id is not None:
        return {
            "id": annotated_id,
            "base_date": getattr(bond, "latest_market_data_base_date", None),
            "price": getattr(bond, "latest_market_data_price", None),
            "substitute_price": getattr(bond, "latest_market_data_substitute_price", None),
            "ytm": getattr(bond, "latest_market_data_ytm", None),
            "duration": getattr(bond, "latest_market_data_duration", None),
            "spread": getattr(bond, "latest_market_data_spread", None),
            "trading_volume": getattr(bond, "latest_market_data_trading_volume", None),
            "bid_yield": getattr(bond, "latest_market_data_bid_yield", None),
            "ask_yield": getattr(bond, "latest_market_data_ask_yield", None),
            "price_change_rate": getattr(bond, "latest_market_data_price_change_rate", None),
        }

    return bond.market_data.filter(deleted_at__isnull=True).order_by("-base_date").first()


def serialize_bond_list_item(bond):
    if is_master_bond(bond):
        return {
            "bond_id": bond.isin_code,
            "isin_code": bond.isin_code,
            "short_code": None,
            "bond_name": bond.bond_name,
            "short_name": None,
            "issuer": {
                "issuer_id": bond.company_id,
                "issuer_name": bond.company_name,
                "industry": {
                    "industry_id": None,
                    "industry_name": bond.industry,
                },
            },
            "bond_type": bond.bond_type,
            "credit_rating": bond.credit_rating,
            "rating_group": rating_group(bond.credit_rating),
            "seniority": bond.seniority,
            "guarantee_status": bond.guarantee_status,
            "coupon_rate": number_or_none(bond.coupon_rate),
            "maturity_date": date_or_none(bond.maturity_date),
            "payment_cycle_months": payment_cycle_months(bond.payment_cycle),
            "interest_type": bond.interest_type,
            "option_type": bond.call_put_option or "NONE",
            "next_exercise_date": None,
            "latest_market_data": None,
        }

    issuer = bond.issuer
    latest_market_data = get_latest_market_data(bond)

    return {
        "bond_id": bond.id,
        "isin_code": bond.isin_code,
        "short_code": bond.short_code,
        "bond_name": bond.bond_name,
        "short_name": bond.short_name,
        "issuer": {
            "issuer_id": issuer.id,
            "issuer_name": issuer.issuer_name,
            "industry": {
                "industry_id": issuer.industry_id,
                "industry_name": issuer.industry.industry_name,
            },
        },
        "bond_type": bond.bond_type.bond_type,
        "credit_rating": bond.rating.rating_name,
        "rating_group": bond.rating.rating_group,
        "seniority": bond.seniority.seniority_name,
        "guarantee_status": bond.guarantee_status.guarantee_status,
        "coupon_rate": number_or_none(bond.coupon_rate),
        "maturity_date": date_or_none(bond.maturity_date),
        "payment_cycle_months": (
            bond.cashflow_rule.interest_payment_unit_months if bond.cashflow_rule_id else None
        ),
        "interest_type": bond.interest_type,
        "option_type": bond.option_exercise.option_type if bond.option_exercise_id else "NONE",
        "next_exercise_date": (
            date_or_none(bond.option_exercise.exercise_start_date_1)
            if bond.option_exercise_id
            else None
        ),
        "latest_market_data": serialize_list_market_data(latest_market_data),
    }


def serialize_bond_detail(bond):
    if is_master_bond(bond):
        return {
            "bond_id": bond.isin_code,
            "basic_info": {
                "isin_code": bond.isin_code,
                "short_code": None,
                "bond_name": bond.bond_name,
                "short_name": None,
                "issuer_name": bond.company_name,
                "industry_name": bond.industry,
                "bond_type": bond.bond_type,
                "credit_rating": bond.credit_rating,
                "rating_group": rating_group(bond.credit_rating),
                "seniority": bond.seniority,
                "guarantee_status": bond.guarantee_status,
            },
            "issue_redemption": {
                "issue_date": date_or_none(bond.issue_date),
                "maturity_date": date_or_none(bond.maturity_date),
                "issue_amount": bond.issue_amount,
                "underwriter": bond.underwriter,
                "redemption_method": None,
                "maturity_redemption_rate": None,
                "early_redemption_description": "",
            },
            "interest_condition": {
                "coupon_rate": number_or_none(bond.coupon_rate),
                "interest_type": bond.interest_type,
                "interest_payment_method": bond.interest_type,
                "interest_payment_unit_months": payment_cycle_months(bond.payment_cycle),
                "interest_calculation_months": payment_cycle_months(bond.payment_cycle),
                "interest_pre_post_type": None,
                "first_interest_payment_date": None,
                "interest_payment_basis": None,
                "interest_month_end_type": None,
            },
            "option_exercise": {
                "option_type": bond.call_put_option or "NONE",
                "exercise_start_date_1": None,
                "exercise_end_date_1": None,
                "exercise_start_date_2": None,
                "exercise_end_date_2": None,
                "call_reason": "",
            },
            "latest_market_data": None,
        }

    cashflow = bond.cashflow_rule
    option = bond.option_exercise

    return {
        "bond_id": bond.id,
        "basic_info": {
            "isin_code": bond.isin_code,
            "short_code": bond.short_code,
            "bond_name": bond.bond_name,
            "short_name": bond.short_name,
            "issuer_name": bond.issuer.issuer_name,
            "industry_name": bond.issuer.industry.industry_name,
            "bond_type": bond.bond_type.bond_type,
            "credit_rating": bond.rating.rating_name,
            "rating_group": bond.rating.rating_group,
            "seniority": bond.seniority.seniority_name,
            "guarantee_status": bond.guarantee_status.guarantee_status,
        },
        "issue_redemption": {
            "issue_date": date_or_none(bond.issue_date),
            "maturity_date": date_or_none(bond.maturity_date),
            "issue_amount": bond.issue_amount,
            "underwriter": bond.underwriter,
            "redemption_method": bond.redemption_method,
            "maturity_redemption_rate": number_or_none(bond.maturity_redemption_rate),
            "early_redemption_description": bond.early_redemption_description,
        },
        "interest_condition": {
            "coupon_rate": number_or_none(bond.coupon_rate),
            "interest_type": bond.interest_type,
            "interest_payment_method": cashflow.interest_payment_method if cashflow else None,
            "interest_payment_unit_months": cashflow.interest_payment_unit_months if cashflow else None,
            "interest_calculation_months": cashflow.interest_calculation_months if cashflow else None,
            "interest_pre_post_type": cashflow.interest_pre_post_type if cashflow else None,
            "first_interest_payment_date": date_or_none(cashflow.first_interest_payment_date) if cashflow else None,
            "interest_payment_basis": cashflow.interest_payment_basis if cashflow else None,
            "interest_month_end_type": cashflow.interest_month_end_type if cashflow else None,
        },
        "option_exercise": {
            "option_type": option.option_type if option else "NONE",
            "exercise_start_date_1": date_or_none(option.exercise_start_date_1) if option else None,
            "exercise_end_date_1": date_or_none(option.exercise_end_date_1) if option else None,
            "exercise_start_date_2": date_or_none(option.exercise_start_date_2) if option else None,
            "exercise_end_date_2": date_or_none(option.exercise_end_date_2) if option else None,
            "call_reason": option.call_reason if option else "",
        },
        "latest_market_data": serialize_market_data(get_latest_market_data(bond)),
    }


def serialize_bond_compare_item(bond):
    if is_master_bond(bond):
        data = serialize_bond_detail(bond)
        basic = data["basic_info"]
        issue = data["issue_redemption"]
        interest = data["interest_condition"]
        option = data["option_exercise"]
        return {
            "bond_id": data["bond_id"],
            "isin_code": basic["isin_code"],
            "short_code": basic["short_code"],
            "bond_name": basic["bond_name"],
            "short_name": basic["short_name"],
            "issuer_name": basic["issuer_name"],
            "industry_name": basic["industry_name"],
            "bond_type": basic["bond_type"],
            "credit_rating": basic["credit_rating"],
            "rating_group": basic["rating_group"],
            "seniority": basic["seniority"],
            "guarantee_status": basic["guarantee_status"],
            "issue_date": issue["issue_date"],
            "maturity_date": issue["maturity_date"],
            "coupon_rate": interest["coupon_rate"],
            "issue_amount": issue["issue_amount"],
            "underwriter": issue["underwriter"],
            "redemption_method": issue["redemption_method"],
            "maturity_redemption_rate": issue["maturity_redemption_rate"],
            "early_redemption_description": issue["early_redemption_description"],
            "interest_type": interest["interest_type"],
            "interest_payment_method": interest["interest_payment_method"],
            "interest_payment_unit_months": interest["interest_payment_unit_months"],
            "interest_calculation_months": interest["interest_calculation_months"],
            "first_interest_payment_date": interest["first_interest_payment_date"],
            "option_type": option["option_type"],
            "next_exercise_date": None,
            "latest_market_data": None,
        }

    latest_market_data = get_latest_market_data(bond)
    cashflow = bond.cashflow_rule
    option = bond.option_exercise

    return {
        "bond_id": bond.id,
        "isin_code": bond.isin_code,
        "short_code": bond.short_code,
        "bond_name": bond.bond_name,
        "short_name": bond.short_name,
        "issuer_name": bond.issuer.issuer_name,
        "industry_name": bond.issuer.industry.industry_name,
        "bond_type": bond.bond_type.bond_type,
        "credit_rating": bond.rating.rating_name,
        "rating_group": bond.rating.rating_group,
        "seniority": bond.seniority.seniority_name,
        "guarantee_status": bond.guarantee_status.guarantee_status,
        "issue_date": date_or_none(bond.issue_date),
        "maturity_date": date_or_none(bond.maturity_date),
        "coupon_rate": number_or_none(bond.coupon_rate),
        "issue_amount": bond.issue_amount,
        "underwriter": bond.underwriter,
        "redemption_method": bond.redemption_method,
        "maturity_redemption_rate": number_or_none(bond.maturity_redemption_rate),
        "early_redemption_description": bond.early_redemption_description,
        "interest_type": bond.interest_type,
        "interest_payment_method": cashflow.interest_payment_method if cashflow else None,
        "interest_payment_unit_months": cashflow.interest_payment_unit_months if cashflow else None,
        "interest_calculation_months": cashflow.interest_calculation_months if cashflow else None,
        "first_interest_payment_date": date_or_none(cashflow.first_interest_payment_date) if cashflow else None,
        "option_type": option.option_type if option else "NONE",
        "next_exercise_date": date_or_none(option.exercise_start_date_1) if option else None,
        "latest_market_data": serialize_market_data(latest_market_data),
    }


def serialize_cashflow_rule(bond):
    if is_master_bond(bond):
        return {
            "bond_id": bond.isin_code,
            "cashflow_rule": {
                "interest_payment_method": bond.interest_type,
                "interest_payment_unit_months": payment_cycle_months(bond.payment_cycle),
                "interest_calculation_months": payment_cycle_months(bond.payment_cycle),
                "interest_pre_post_type": None,
                "first_interest_payment_date": None,
                "interest_payment_basis": None,
                "interest_month_end_type": None,
            },
        }

    cashflow = bond.cashflow_rule
    if cashflow is None:
        return {"bond_id": bond.id, "cashflow_rule": None}

    return {
        "bond_id": bond.id,
        "cashflow_rule": {
            "interest_payment_method": cashflow.interest_payment_method,
            "interest_payment_unit_months": cashflow.interest_payment_unit_months,
            "interest_calculation_months": cashflow.interest_calculation_months,
            "interest_pre_post_type": cashflow.interest_pre_post_type,
            "first_interest_payment_date": date_or_none(cashflow.first_interest_payment_date),
            "interest_payment_basis": cashflow.interest_payment_basis,
            "interest_month_end_type": cashflow.interest_month_end_type,
        },
    }
