from apps.bonds.serializers import serialize_bond_list_item
from apps.indicators.serializers import serialize_credit_rating_rate
from apps.news.serializers import serialize_news_list_item


def format_percent(value):
    if value is None:
        return "-"
    return f"{float(value):.2f}%"


def serialize_home_bond(bond):
    item = serialize_bond_list_item(bond)
    market_data = item.get("latest_market_data") or {}
    return {
        "bond_id": item["bond_id"],
        "name": item["bond_name"],
        "short_name": item["short_name"],
        "code": item["isin_code"],
        "short_code": item["short_code"],
        "issuer_name": item["issuer"]["issuer_name"],
        "industry_name": item["issuer"]["industry"]["industry_name"],
        "type": item["bond_type"],
        "rating": item["credit_rating"],
        "rating_group": item["rating_group"],
        "maturity_date": item["maturity_date"],
        "coupon_rate": item["coupon_rate"],
        "interest_cycle_months": item["payment_cycle_months"],
        "buy_yield": market_data.get("bid_yield"),
        "ytm": market_data.get("ytm"),
        "price": market_data.get("price"),
        "latest_market_data": market_data,
    }


def serialize_indicator_cards(base_rates, deposit_rates, credit_rates):
    korea_rate = next((item for item in base_rates if item.country.country_name in ("한국", "대한민국")), None)
    treasury = korea_rate or (base_rates[0] if base_rates else None)
    credit_rate_items = [serialize_credit_rating_rate(row) for row in credit_rates]

    return [
        {
            "id": "treasury-rate",
            "title": "국고채 / 미국채 금리",
            "value": format_percent(treasury.ten_year_yield if treasury else None),
            "caption": "10년물 기준",
            "rows": [
                ["3년", format_percent(treasury.three_year_yield if treasury else None)],
                ["10년", format_percent(treasury.ten_year_yield if treasury else None)],
            ],
        },
        {
            "id": "central-bank-rate",
            "title": "국가별 기준 금리",
            "value": format_percent(korea_rate.base_interest_rate if korea_rate else None),
            "caption": "주요국 통화정책 비교",
            "rows": [
                [item.country.country_name, format_percent(item.base_interest_rate)]
                for item in base_rates[:3]
            ],
        },
        {
            "id": "credit-rating-yield",
            "title": "신용등급별 평균 금리",
            "value": format_percent(credit_rate_items[0]["average_ytm"] if credit_rate_items else None),
            "caption": "시장 데이터 기준 평균 YTM",
            "rows": [
                [item["credit_rating"], format_percent(item["average_ytm"])]
                for item in credit_rate_items[:3]
            ],
        },
        {
            "id": "deposit-compare",
            "title": "예금 금리 비교",
            "value": format_percent(deposit_rates[0].prime_rate if deposit_rates else None),
            "caption": "우대금리 높은 순",
            "rows": [
                [item.bank.bank_name, format_percent(item.prime_rate)]
                for item in deposit_rates[:3]
            ],
        },
        {
            "id": "yield-spread",
            "title": "장단기 금리차",
            "value": format_percent(treasury.yield_curve_spread if treasury else None),
            "caption": "10년-3년 스프레드",
            "rows": [
                [item.country.country_name, format_percent(item.yield_curve_spread)]
                for item in base_rates[:3]
            ],
        },
    ]


def serialize_home_payload(bonds, news, base_rates, deposit_rates, credit_rates):
    return {
        "search": {
            "popular_keywords": ["국고채", "고수익", "안정형", "콜옵션"],
            "filters": [
                {"key": "bondTypes", "label": "채권 종류", "options": ["국채", "회사채", "금융채"]},
                {"key": "maturities", "label": "만기", "options": ["1년 이하", "1~3년", "3~5년", "5~10년", "10년 이상"]},
                {"key": "yields", "label": "수익률", "options": ["3% 이상", "4% 이상", "5% 이상", "6% 이상"]},
                {"key": "ratings", "label": "신용등급", "options": ["AAA", "AA", "A", "BBB"]},
                {"key": "interestCycles", "label": "이자 지급 주기", "options": ["3개월", "6개월", "12개월", "만기일시"]},
            ],
        },
        "indicators": serialize_indicator_cards(base_rates, deposit_rates, credit_rates),
        "curated_bonds": [serialize_home_bond(bond) for bond in bonds],
        "latest_news": [serialize_news_list_item(item) for item in news],
        "guide_links": [
            {"guide_id": "what", "title": "채권이란?", "path": "/guide/what"},
            {"guide_id": "risk", "title": "채권 투자 위험", "path": "/guide/risk"},
            {"guide_id": "dictionary", "title": "용어 사전", "path": "/dictionary"},
        ],
    }

