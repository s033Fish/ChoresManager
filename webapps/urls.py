from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from chores_manager import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name='signup'),
    path("privacy/", views.privacy, name="privacy"),
    path("data-deletion/", views.datadeletion, name="data-deletion"),
]
