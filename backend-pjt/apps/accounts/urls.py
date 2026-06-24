from django.urls import path

from . import views

urlpatterns = [
    path("auth/signup", views.signup, name="auth-signup"),
    path("auth/register", views.signup, name="auth-register"),
    path("auth/login", views.login, name="auth-login"),
    path("auth/logout", views.logout, name="auth-logout"),
    path("auth/me", views.me, name="auth-me"),
    path("me", views.me, name="me"),
]
