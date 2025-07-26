from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Pages publiques
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="streams/login.html"),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    # Dashboard utilisateur
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create-live/", views.create_live, name="create_live"),
    # Actions sur les lives
    path("live/<int:live_id>/start/", views.start_live, name="start_live"),
    path("live/<int:live_id>/stop/", views.stop_live, name="stop_live"),
    # Dashboard admin
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-users/", views.admin_users, name="admin_users"),
    path("approve-user/<int:user_id>/", views.approve_user, name="approve_user"),
    path("reject-user/<int:user_id>/", views.reject_user, name="reject_user"),
    path("toggle-admin/<int:user_id>/", views.toggle_admin, name="toggle_admin"),
    path("delete-user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("upload-chunk/", views.upload_chunk, name="upload_chunk"),
]
