import django.db.models.deletion
from django.db import migrations, models


CREATE_LATEST_BOND_MARKET_DATA_VIEW = """
CREATE OR REPLACE VIEW latest_bond_market_data AS
SELECT DISTINCT ON (bond_id)
    market_data_id,
    bond_id,
    base_date,
    price,
    ytm,
    duration,
    spread,
    trading_volume,
    substitute_price,
    bid_yield,
    ask_yield,
    price_change_rate
FROM bond_market_data
WHERE deleted_at IS NULL
ORDER BY bond_id, base_date DESC, market_data_id DESC;
"""


DROP_LATEST_BOND_MARKET_DATA_VIEW = """
DROP VIEW IF EXISTS latest_bond_market_data;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("bonds", "0002_bondsmaster_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="LatestBondMarketData",
            fields=[
                ("id", models.BigIntegerField(db_column="market_data_id", primary_key=True, serialize=False)),
                ("base_date", models.DateField()),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("ytm", models.DecimalField(blank=True, decimal_places=3, max_digits=6, null=True)),
                ("duration", models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ("spread", models.DecimalField(blank=True, decimal_places=7, max_digits=8, null=True)),
                ("trading_volume", models.BigIntegerField(blank=True, null=True)),
                ("substitute_price", models.CharField(blank=True, max_length=255, null=True)),
                ("bid_yield", models.CharField(blank=True, max_length=255, null=True)),
                ("ask_yield", models.CharField(blank=True, max_length=255, null=True)),
                ("price_change_rate", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "bond",
                    models.OneToOneField(
                        db_column="bond_id",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="latest_market_data",
                        to="bonds.bond",
                    ),
                ),
            ],
            options={
                "db_table": "latest_bond_market_data",
                "managed": False,
            },
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS bond_market_data_latest_idx
            ON bond_market_data (bond_id, base_date DESC, market_data_id DESC)
            WHERE deleted_at IS NULL;
            """,
            reverse_sql="DROP INDEX IF EXISTS bond_market_data_latest_idx;",
        ),
        migrations.RunSQL(
            sql=CREATE_LATEST_BOND_MARKET_DATA_VIEW,
            reverse_sql=DROP_LATEST_BOND_MARKET_DATA_VIEW,
        ),
    ]
