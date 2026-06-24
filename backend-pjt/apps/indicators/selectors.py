from django.db.models import Avg, Count, OuterRef, Subquery

from apps.bonds.models import Bond

from .models import BaseRate, DepositRate


def latest_base_rates():
    base_queryset = BaseRate.objects.filter(
        deleted_at__isnull=True,
        country__deleted_at__isnull=True,
    )
    latest_id_by_country = (
        base_queryset
        .filter(country_id=OuterRef("country_id"))
        .order_by("-created_at", "-id")
        .values("id")[:1]
    )

    return (
        base_queryset
        .filter(id=Subquery(latest_id_by_country))
        .select_related("country")
        .order_by("country__country_name")
    )


def latest_deposit_rates():
    return (
        DepositRate.objects.filter(deleted_at__isnull=True, bank__deleted_at__isnull=True)
        .select_related("bank")
        .order_by("-prime_rate", "bank__bank_name")
    )


def credit_rating_rates():
    return (
        Bond.objects.filter(
            deleted_at__isnull=True,
            rating__deleted_at__isnull=True,
            coupon_rate__gt=0,
        )
        .values("rating__rating_name")
        .annotate(average_ytm=Avg("coupon_rate"), bond_count=Count("id", distinct=True))
        .order_by("rating__rating_order")
    )

