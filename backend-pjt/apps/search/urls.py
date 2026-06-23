from django.urls import path

from . import views

urlpatterns = [
    path("search/bonds", views.bond_search, name="bond-search"),
]
