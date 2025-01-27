from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from chores_manager import views, admin_views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name='signup'),
    path("privacy/", views.privacy, name="privacy"),
    path("data-deletion/", views.datadeletion, name="data-deletion"),
    path("terms/", views.terms, name="terms"),
    path('sms/reply/', views.sms_reply_webhook, name='sms_reply_webhook'),
    path('admin-panel/', admin_views.admin_panel, name='admin_panel'),
    path('admin-actions/add-chores/', admin_views.add_chores, name='add_chores'),
    path('admin-actions/assign-chores/', admin_views.assign_chores, name='assign_chores'),
    path('admin-actions/send-sms/', admin_views.send_sms_reminders, name='send_sms'),

]
