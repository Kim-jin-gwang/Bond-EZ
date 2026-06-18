from django.utils import timezone

from .models import UserBond


def create_or_update_user_bond(user, bond, data):
    defaults = {
        "purchase_price": data.get("purchase_price"),
        "purchase_date": data.get("purchase_date"),
        "quantity": data.get("quantity") or 0,
        "deleted_at": None,
    }
    user_bond, _ = UserBond.objects.update_or_create(
        user=user,
        bond=bond,
        defaults=defaults,
    )
    return user_bond


def delete_user_bond(user_bond):
    user_bond.deleted_at = timezone.now()
    user_bond.save(update_fields=["deleted_at", "updated_at"])

