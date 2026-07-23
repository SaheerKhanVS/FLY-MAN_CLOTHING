from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/create/", views.staff_create, name="staff_create"),
    path("staff/export/", views.staff_export, name="staff_export"),
    path("staff/<int:pk>/", views.staff_profile, name="staff_profile"),
    path("staff/<int:pk>/edit/", views.staff_edit, name="staff_edit"),
    path("staff/<int:pk>/delete/", views.staff_delete, name="staff_delete"),
    path("staff/<int:pk>/activate/", views.staff_activate, name="staff_activate"),
    path("staff/<int:pk>/deactivate/", views.staff_deactivate, name="staff_deactivate"),
]
