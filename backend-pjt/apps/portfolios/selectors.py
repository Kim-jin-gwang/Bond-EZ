from django.db.models import Prefetch

from apps.bonds.selectors import base_bond_queryset

from .models import UserBond


def user_bonds_for(user):
    return (
        UserBond.objects.filter(user=user, deleted_at__isnull=True)
        .select_related("user")
        .prefetch_related(Prefetch("bond", queryset=base_bond_queryset()))
        .order_by("-created_at")
    )


def get_user_bond(user, user_bond_id):
    return (
        UserBond.objects.filter(id=user_bond_id, user=user, deleted_at__isnull=True)
        .select_related("user")
        .prefetch_related(Prefetch("bond", queryset=base_bond_queryset()))
        .first()
    )


def get_active_bond_for_portfolio(bond_id):
    return base_bond_queryset().filter(id=bond_id).first()
