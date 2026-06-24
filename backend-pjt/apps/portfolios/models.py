from django.conf import settings
from django.db import models

from apps.bonds.models import Bond


class UserBond(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_bonds")
    bond = models.ForeignKey(Bond, on_delete=models.CASCADE, related_name="user_bonds")
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_bond"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "bond"],
                condition=models.Q(deleted_at__isnull=True),
                name="uniq_active_user_bond",
            )
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["bond"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.bond_id}"

