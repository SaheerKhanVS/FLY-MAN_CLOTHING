from django.urls import path
from .views import company_profile, dashboard, edit_company, export_company_pdf

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('company-profile/', company_profile, name='company_profile'),
    path('company-export-pdf/', export_company_pdf, name='company_export_pdf'),
    path('company-edit/', edit_company, name='edit_company')
]