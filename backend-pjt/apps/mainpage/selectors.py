from apps.bonds.selectors import filtered_bonds
from apps.indicators.selectors import credit_rating_rates, latest_base_rates, latest_deposit_rates
from apps.news.selectors import filtered_news


def beginner_bonds(limit=4):
    queryset = filtered_bonds({"sort": "maturity_asc"})
    return queryset[:limit]


def latest_news(limit=3):
    return filtered_news({})[:limit]


def main_base_rates():
    return list(latest_base_rates()[:5])


def main_deposit_rates():
    return list(latest_deposit_rates()[:3])


def main_credit_rating_rates():
    return list(credit_rating_rates()[:4])

