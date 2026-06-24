from django.contrib import admin
from .models import Company, SystemSettings


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "owner_name",
        "phone",
        "email",
        "city",
        "country",
    )
    search_fields = (
        "company_name",
        "owner_name",
        "phone",
        "email",
    )


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "currency",
        "allow_negative_balance",
        "default_commission",
    )