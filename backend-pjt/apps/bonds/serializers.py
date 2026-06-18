def number_or_none(value):
    return None if value is None else float(value)


def date_or_none(value):
    return None if value is None else value.isoformat()


def serialize_market_data(market_data):
    if market_data is None:
        return None

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


def get_latest_market_data(bond):
    cached = getattr(bond, "prefetched_latest_market_data", None)
    if cached is not None:
        return cached[0] if cached else None
    return bond.market_data.filter(deleted_at__isnull=True).order_by("-base_date").first()


def serialize_bond_list_item(bond):
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
        "latest_market_data": serialize_market_data(latest_market_data),
    }


def serialize_bond_detail(bond):
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
