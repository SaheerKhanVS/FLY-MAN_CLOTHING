from django.urls import path
from . import views

urlpatterns = [
    path("parties/", views.party_list, name="party_list"),
    path("parties/create/", views.party_create, name="party_create"),
    path("parties/<int:pk>/", views.party_detail, name="party_detail"),
    path("parties/<int:pk>/edit/", views.party_edit, name="party_edit"),
    path("parties/<int:pk>/delete/", views.party_delete, name="party_delete"),
    path("parties/api/pincode/<str:pincode>/", views.pincode_lookup_api, name="pincode_lookup_api"),
    path("parties/api/party-type/create/", views.create_party_type_api, name="create_party_type_api"),
    path("parties/api/party-types/", views.get_party_types_api, name="get_party_types_api"),
    path("parties/api/party-type/<int:pk>/edit/", views.edit_party_type_api, name="edit_party_type_api"),
    path("parties/api/party-type/<int:pk>/delete/", views.delete_party_type_api, name="delete_party_type_api"),
]
