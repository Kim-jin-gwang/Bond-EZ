from django.urls import path

from . import views

urlpatterns = [
    path("glossary/categories", views.category_list, name="glossary-category-list"),
    path("glossary", views.glossary_list, name="glossary-list"),
    path("glossary/<int:term_id>", views.glossary_detail, name="glossary-detail"),
]

