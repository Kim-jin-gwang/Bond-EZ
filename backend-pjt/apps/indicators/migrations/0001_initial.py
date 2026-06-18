# Generated manually for the indicator APIs.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Bank",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bank_name", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "bank", "indexes": [models.Index(fields=["bank_name"], name="bank_bank_na_e0d24a_idx")]},
        ),
        migrations.CreateModel(
            name="Country",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("country_name", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "country", "indexes": [models.Index(fields=["country_name"], name="country_countr_223010_idx")]},
        ),
        migrations.CreateModel(
            name="DepositRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=200)),
                ("base_rate", models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                ("prime_rate", models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("bank", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="deposit_rates", to="indicators.bank")),
            ],
            options={
                "db_table": "deposit_rate",
                "indexes": [
                    models.Index(fields=["bank"], name="deposit_rat_bank_id_536c8f_idx"),
                    models.Index(fields=["prime_rate"], name="deposit_rat_prime_r_e501b9_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="BaseRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("base_interest_rate", models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                ("three_year_yield", models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                ("ten_year_yield", models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                ("yield_curve_spread", models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("country", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="base_rates", to="indicators.country")),
            ],
            options={
                "db_table": "base_rate",
                "indexes": [
                    models.Index(fields=["country", "-created_at"], name="base_rate_country_1ff6e8_idx"),
                    models.Index(fields=["created_at"], name="base_rate_created_52e607_idx"),
                ],
            },
        ),
    ]
