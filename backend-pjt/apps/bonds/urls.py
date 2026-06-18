from django.urls import path

from . import views

urlpatterns = [
    path("bonds", views.bond_list, name="bond-list"),
    path("bonds/compare", views.bond_compare, name="bond-compare"),
    path("bonds/filter-options", views.bond_filter_options, name="bond-filter-options"),
    path("bonds/<int:bond_id>", views.bond_detail, name="bond-detail"),
    path("bonds/<int:bond_id>/cashflows", views.bond_cashflows, name="bond-cashflows"),
    path("bonds/<int:bond_id>/market-data", views.bond_market_data_history, name="bond-market-data"),
    path(
        "bonds/<int:bond_id>/market-data/latest",
        views.bond_latest_market_data,
        name="bond-latest-market-data",
    ),
]
