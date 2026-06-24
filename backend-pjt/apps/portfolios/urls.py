from django.urls import path

from . import views

urlpatterns = [
    path("me/bonds", views.my_bonds, name="my-bonds"),
    path("me/bonds/<int:user_bond_id>", views.my_bond_delete, name="my-bond-delete"),
    path("me/favorites", views.my_favorites, name="my-favorites"),
    path("me/favorites/<str:bond_id>", views.my_favorite_delete, name="my-favorite-delete"),
]


