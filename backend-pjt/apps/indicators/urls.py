from django.urls import path

from . import views

urlpatterns = [
    path("indicators", views.indicator_summary, name="indicator-summary"),
    path("base-rates", views.base_rate_list, name="base-rate-list"),
    path("base-rates/treasury-rates", views.treasury_rates, name="treasury-rates"),
    path("base-rates/yield-spreads", views.yield_spreads, name="yield-spreads"),
    path("base-rates/yield-curve", views.yield_curve, name="yield-curve"),
    path("deposit-rates", views.deposit_rate_list, name="deposit-rate-list"),
    path("credit-ratings/rates", views.credit_rating_rate_list, name="credit-rating-rates"),
]

