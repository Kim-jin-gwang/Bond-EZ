# Generated manually for the portfolio API.

import django.conf
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
        ("bonds", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserBond",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purchase_price", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("purchase_date", models.DateField(blank=True, null=True)),
                ("quantity", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("bond", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_bonds", to="bonds.bond")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_bonds", to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "user_bond",
                "indexes": [
                    models.Index(fields=["user"], name="user_bond_user_id_7b7ea7_idx"),
                    models.Index(fields=["bond"], name="user_bond_bond_id_daf87d_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(condition=models.Q(("deleted_at__isnull", True)), fields=("user", "bond"), name="uniq_active_user_bond")
                ],
            },
        ),
    ]
