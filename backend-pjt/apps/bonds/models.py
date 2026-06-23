from django.db import models


class TimeStampedSoftDeleteModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class Industry(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="industry_id")
    industry_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = "industry"

    def __str__(self):
        return self.industry_name


class Issuer(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="issuer_id")
    industry = models.ForeignKey(Industry, on_delete=models.PROTECT, related_name="issuers", db_column="industry_id")
    issuer_name = models.CharField(max_length=100)
    crno = models.CharField(max_length=50, blank=True)

    class Meta:
        managed = False
        db_table = "issuer"
        indexes = [models.Index(fields=["issuer_name"])]

    def __str__(self):
        return self.issuer_name


class BondType(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="bond_type_id")
    bond_type = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "bond_type"

    def __str__(self):
        return self.bond_type


class Seniority(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="seniority_id")
    seniority_name = models.CharField(max_length=20)
    priority_order = models.BigIntegerField(default=0)

    class Meta:
        managed = False
        db_table = "seniority"

    def __str__(self):
        return self.seniority_name


class GuaranteeStatus(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="guarantee_status_id")
    guarantee_status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = "guarantee_status"

    def __str__(self):
        return self.guarantee_status


class CreditRating(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="rating_id")
    rating_name = models.CharField(max_length=30)
    rating_order = models.PositiveIntegerField(default=0)

    class Meta:
        managed = False
        db_table = "credit_rating"
        indexes = [models.Index(fields=["rating_name"]), models.Index(fields=["rating_order"])]

    @property
    def rating_group(self):
        return self.rating_name.rstrip("+-0123456789")

    def __str__(self):
        return self.rating_name


class BondCashflowRule(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="cashflow_rule_id")
    interest_payment_method = models.CharField(max_length=255, blank=True)
    interest_payment_unit_months = models.CharField(max_length=255, null=True, blank=True)
    interest_calculation_months = models.CharField(max_length=255, null=True, blank=True)
    interest_pre_post_type = models.CharField(max_length=255, blank=True)
    first_interest_payment_date = models.DateField(null=True, blank=True)
    interest_payment_basis = models.CharField(max_length=255, blank=True)
    interest_month_end_type = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = "bond_cashflow_rule"


class BondOptionExercise(TimeStampedSoftDeleteModel):
    class OptionType(models.TextChoices):
        NONE = "옵션해당사항없음", "없음"
        CALL = "CALL", "CALL"
        PUT = "PUT", "PUT"
        CALL_PUT = "CALL+PUT", "CALL+PUT"

    id = models.BigIntegerField(primary_key=True, db_column="option_exercise_id")
    option_type = models.CharField(max_length=20, choices=OptionType.choices, default=OptionType.NONE)
    exercise_start_date_1 = models.DateField(null=True, blank=True)
    exercise_end_date_1 = models.DateField(null=True, blank=True)
    exercise_start_date_2 = models.DateField(null=True, blank=True)
    exercise_end_date_2 = models.DateField(null=True, blank=True)
    call_reason = models.TextField(blank=True, db_column="exercise_reason")

    class Meta:
        managed = False
        db_table = "bond_option_exercise"
        indexes = [models.Index(fields=["option_type"])]


class Bond(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="bond_id")
    isin_code = models.CharField(max_length=255, unique=True)
    bond_type = models.ForeignKey(BondType, on_delete=models.PROTECT, related_name="bonds", db_column="bond_type_id")
    short_code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    bond_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True)
    issuer = models.ForeignKey(Issuer, on_delete=models.PROTECT, related_name="bonds", db_column="issuer_id")
    issue_date = models.DateField()
    maturity_date = models.DateField()
    coupon_rate = models.DecimalField(max_digits=10, decimal_places=4)
    issue_amount = models.BigIntegerField(null=True, blank=True)
    underwriter = models.CharField(max_length=255, blank=True)
    interest_type = models.CharField(max_length=100, blank=True)
    option_type = models.CharField(max_length=20, blank=True)
    payment_cycle_months = models.PositiveIntegerField(null=True, blank=True)
    cashflow_rule = models.ForeignKey(
        BondCashflowRule,
        on_delete=models.PROTECT,
        related_name="bonds",
        null=True,
        blank=True,
        db_column="cashflow_rule_id",
    )
    maturity_redemption_rate = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    redemption_method = models.CharField(max_length=255, blank=True)
    early_redemption_description = models.TextField(blank=True)
    seniority = models.ForeignKey(Seniority, on_delete=models.PROTECT, related_name="bonds")
    option_exercise = models.ForeignKey(
        BondOptionExercise,
        on_delete=models.PROTECT,
        related_name="bonds",
        null=True,
        blank=True,
        db_column="option_exercise_id",
    )
    guarantee_status = models.ForeignKey(
        GuaranteeStatus,
        on_delete=models.PROTECT,
        related_name="bonds",
        db_column="guarantee_status_id",
    )
    rating = models.ForeignKey(CreditRating, on_delete=models.PROTECT, related_name="bonds", db_column="rating_id")

    class Meta:
        managed = False
        db_table = "bond"
        indexes = [
            models.Index(fields=["bond_name"]),
            models.Index(fields=["short_name"]),
            models.Index(fields=["issuer"]),
            models.Index(fields=["bond_type"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["maturity_date"]),
        ]

    def __str__(self):
        return self.bond_name


class BondMarketData(TimeStampedSoftDeleteModel):
    id = models.BigIntegerField(primary_key=True, db_column="market_data_id")
    bond = models.ForeignKey(Bond, on_delete=models.CASCADE, related_name="market_data", db_column="bond_id")
    base_date = models.DateField()
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ytm = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    duration = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    spread = models.DecimalField(max_digits=8, decimal_places=7, null=True, blank=True)
    trading_volume = models.BigIntegerField(null=True, blank=True)
    substitute_price = models.CharField(max_length=255, null=True, blank=True)
    bid_yield = models.CharField(max_length=255, null=True, blank=True)
    ask_yield = models.CharField(max_length=255, null=True, blank=True)
    price_change_rate = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "bond_market_data"
        constraints = [
            models.UniqueConstraint(fields=["bond", "base_date"], name="uniq_bond_market_data_date")
        ]
        indexes = [
            models.Index(fields=["bond", "-base_date"]),
            models.Index(fields=["base_date"]),
            models.Index(fields=["ytm"]),
            models.Index(fields=["trading_volume"]),
        ]


class LatestBondMarketData(models.Model):
    id = models.BigIntegerField(primary_key=True, db_column="market_data_id")
    bond = models.OneToOneField(
        Bond,
        on_delete=models.DO_NOTHING,
        related_name="latest_market_data",
        db_column="bond_id",
    )
    base_date = models.DateField()
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ytm = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    duration = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    spread = models.DecimalField(max_digits=8, decimal_places=7, null=True, blank=True)
    trading_volume = models.BigIntegerField(null=True, blank=True)
    substitute_price = models.CharField(max_length=255, null=True, blank=True)
    bid_yield = models.CharField(max_length=255, null=True, blank=True)
    ask_yield = models.CharField(max_length=255, null=True, blank=True)
    price_change_rate = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "latest_bond_market_data"


class BondsMaster(models.Model):
    isin_code = models.CharField(max_length=255, primary_key=True)
    bond_name = models.CharField(max_length=255)
    company_id = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    issue_date = models.DateField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    coupon_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    issue_amount = models.BigIntegerField(null=True, blank=True)
    bond_type = models.CharField(max_length=255, blank=True, null=True)
    seniority = models.CharField(max_length=255, blank=True, null=True)
    call_put_option = models.CharField(max_length=255, blank=True, null=True)
    interest_type = models.CharField(max_length=255, blank=True, null=True)
    payment_cycle = models.CharField(max_length=255, blank=True, null=True)
    guarantee_status = models.CharField(max_length=255, blank=True, null=True)
    underwriter = models.CharField(max_length=255, blank=True, null=True)
    credit_rating = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "bonds_master"
        indexes = [
            models.Index(fields=["bond_name"]),
            models.Index(fields=["company_name"]),
            models.Index(fields=["maturity_date"]),
        ]
