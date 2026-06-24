from django.urls import path

from . import views

urlpatterns = [
    path("news", views.news_list, name="news-list"),
    path("news/providers", views.provider_list, name="news-provider-list"),
    path("news/<int:news_id>", views.news_detail, name="news-detail"),
]

