from django.urls import path
from .views import (
    company_profile,
    dashboard,
    edit_company,
    export_company_pdf,
    settings,
    color_search_api,
    color_create_api,
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('company-profile/', company_profile, name='company_profile'),
    path('company-export-pdf/', export_company_pdf, name='company_export_pdf'),
    path('company-edit/', edit_company, name='edit_company'),
    path('settings/', settings, name='settings'),
    path('colors/search/', color_search_api, name='color_search_api'),
    path('colors/create/', color_create_api, name='color_create_api'),
]