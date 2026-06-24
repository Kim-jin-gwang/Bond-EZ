# Generated manually for the bond domain API.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BondCashflowRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("interest_payment_method", models.CharField(blank=True, max_length=255)),
                ("interest_payment_unit_months", models.PositiveIntegerField(blank=True, null=True)),
                ("interest_calculation_months", models.PositiveIntegerField(blank=True, null=True)),
                ("interest_pre_post_type", models.CharField(blank=True, max_length=255)),
                ("first_interest_payment_date", models.DateField(blank=True, null=True)),
                ("interest_payment_basis", models.CharField(blank=True, max_length=255)),
                ("interest_month_end_type", models.CharField(blank=True, max_length=255)),
            ],
            options={"db_table": "bond_cashflow_rule"},
        ),
        migrations.CreateModel(
            name="BondOptionExercise",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "option_type",
                    models.CharField(
                        choices=[("NONE", "없음"), ("CALL", "CALL"), ("PUT", "PUT"), ("CALL+PUT", "CALL+PUT")],
                        default="NONE",
                        max_length=20,
                    ),
                ),
                ("exercise_start_date_1", models.DateField(blank=True, null=True)),
                ("exercise_end_date_1", models.DateField(blank=True, null=True)),
                ("exercise_start_date_2", models.DateField(blank=True, null=True)),
                ("exercise_end_date_2", models.DateField(blank=True, null=True)),
                ("call_reason", models.TextField(blank=True)),
            ],
            options={"db_table": "bond_option_exercise", "indexes": [models.Index(fields=["option_type"], name="bond_option_option__9d7739_idx")]},
        ),
        migrations.CreateModel(
            name="BondType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("bond_type", models.CharField(max_length=100)),
            ],
            options={"db_table": "bond_type"},
        ),
        migrations.CreateModel(
            name="CreditRating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("rating_name", models.CharField(max_length=30)),
                ("rating_order", models.PositiveIntegerField(default=0)),
            ],
            options={"db_table": "credit_rating", "indexes": [models.Index(fields=["rating_name"], name="credit_rati_rating__04e2e5_idx"), models.Index(fields=["rating_order"], name="credit_rati_rating__b0e1f2_idx")]},
        ),
        migrations.CreateModel(
            name="GuaranteeStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("guarantee_status", models.CharField(max_length=20)),
            ],
            options={"db_table": "guarantee_status"},
        ),
        migrations.CreateModel(
            name="Industry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("industry_name", models.CharField(max_length=50)),
            ],
            options={"db_table": "industry"},
        ),
        migrations.CreateModel(
            name="Seniority",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("seniority_name", models.CharField(max_length=20)),
            ],
            options={"db_table": "seniority"},
        ),
        migrations.CreateModel(
            name="Issuer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("issuer_name", models.CharField(max_length=100)),
                ("industry", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="issuers", to="bonds.industry")),
            ],
            options={"db_table": "issuer", "indexes": [models.Index(fields=["issuer_name"], name="issuer_issuer__4e9f0d_idx")]},
        ),
        migrations.CreateModel(
            name="Bond",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("isin_code", models.CharField(max_length=255, unique=True)),
                ("short_code", models.CharField(max_length=255, unique=True)),
                ("bond_name", models.CharField(max_length=255)),
                ("short_name", models.CharField(blank=True, max_length=255)),
                ("issue_date", models.DateField()),
                ("maturity_date", models.DateField()),
                ("coupon_rate", models.DecimalField(decimal_places=4, max_digits=10)),
                ("issue_amount", models.BigIntegerField(blank=True, null=True)),
                ("underwriter", models.CharField(blank=True, max_length=255)),
                ("interest_type", models.CharField(blank=True, max_length=100)),
                ("maturity_redemption_rate", models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ("redemption_method", models.CharField(blank=True, max_length=255)),
                ("early_redemption_description", models.TextField(blank=True)),
                ("bond_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bonds", to="bonds.bondtype")),
                ("cashflow_rule", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="bonds", to="bonds.bondcashflowrule")),
                ("guarantee_status", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bonds", to="bonds.guaranteestatus")),
                ("issuer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bonds", to="bonds.issuer")),
                ("option_exercise", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="bonds", to="bonds.bondoptionexercise")),
                ("rating", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bonds", to="bonds.creditrating")),
                ("seniority", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bonds", to="bonds.seniority")),
            ],
            options={"db_table": "bond", "indexes": [models.Index(fields=["bond_name"], name="bond_bond_na_03fef6_idx"), models.Index(fields=["short_name"], name="bond_short_n_8d3189_idx"), models.Index(fields=["issuer"], name="bond_issuer__c6e37f_idx"), models.Index(fields=["bond_type"], name="bond_bond_ty_afb377_idx"), models.Index(fields=["rating"], name="bond_rating__83914b_idx"), models.Index(fields=["maturity_date"], name="bond_maturit_aa0e5f_idx")]},
        ),
        migrations.CreateModel(
            name="BondMarketData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("base_date", models.DateField()),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("ytm", models.DecimalField(blank=True, decimal_places=3, max_digits=6, null=True)),
                ("duration", models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ("spread", models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ("trading_volume", models.BigIntegerField(blank=True, null=True)),
                ("substitute_price", models.PositiveIntegerField(blank=True, null=True)),
                ("bid_yield", models.DecimalField(blank=True, decimal_places=3, max_digits=6, null=True)),
                ("ask_yield", models.DecimalField(blank=True, decimal_places=3, max_digits=6, null=True)),
                ("price_change_rate", models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ("bond", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_data", to="bonds.bond")),
            ],
            options={
                "db_table": "bond_market_data",
                "indexes": [
                    models.Index(fields=["bond", "-base_date"], name="bond_market_bond_id_eb4c3d_idx"),
                    models.Index(fields=["base_date"], name="bond_market_base_da_7221ab_idx"),
                    models.Index(fields=["ytm"], name="bond_market_ytm_700207_idx"),
                    models.Index(fields=["trading_volume"], name="bond_market_trading_cfa8f5_idx"),
                ],
                "constraints": [models.UniqueConstraint(fields=("bond", "base_date"), name="uniq_bond_market_data_date")],
            },
        ),
    ]
