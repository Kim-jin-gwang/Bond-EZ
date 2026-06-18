from django.db.models import Avg, Count

from apps.bonds.models import BondMarketData

from .models import BaseRate, DepositRate


def latest_base_rates():
    return (
        BaseRate.objects.filter(deleted_at__isnull=True, country__deleted_at__isnull=True)
        .select_related("country")
        .order_by("country__country_name", "-created_at")
    )


def latest_deposit_rates():
    return (
        DepositRate.objects.filter(deleted_at__isnull=True, bank__deleted_at__isnull=True)
        .select_related("bank")
        .order_by("-prime_rate", "bank__bank_name")
    )


def credit_rating_rates():
    return (
        BondMarketData.objects.filter(
            deleted_at__isnull=True,
            bond__deleted_at__isnull=True,
            bond__rating__deleted_at__isnull=True,
        )
        .values("bond__rating__rating_name")
        .annotate(average_ytm=Avg("ytm"), bond_count=Count("bond_id", distinct=True))
        .order_by("bond__rating__rating_order")
    )

