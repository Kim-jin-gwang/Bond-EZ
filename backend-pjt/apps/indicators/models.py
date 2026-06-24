from django.db import models


class Country(models.Model):
    country_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "country"
        indexes = [models.Index(fields=["country_name"])]

    def __str__(self):
        return self.country_name


class BaseRate(models.Model):
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="base_rates")
    base_interest_rate = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    three_year_yield = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    ten_year_yield = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    yield_curve_spread = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "base_rate"
        indexes = [
            models.Index(fields=["country", "-created_at"]),
            models.Index(fields=["created_at"]),
        ]


class Bank(models.Model):
    bank_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bank"
        indexes = [models.Index(fields=["bank_name"])]

    def __str__(self):
        return self.bank_name


class DepositRate(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name="deposit_rates")
    product_name = models.CharField(max_length=200)
    base_rate = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    prime_rate = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "deposit_rate"
        indexes = [
            models.Index(fields=["bank"]),
            models.Index(fields=["prime_rate"]),
        ]

