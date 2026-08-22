from django.contrib import admin
from .models import Party, PartyType


@admin.register(PartyType)
class PartyTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("name", "party_type", "phone_1", "company_name", "balance", "created_at")
    list_filter = ("party_type",)
    search_fields = ("name", "phone_1", "company_name", "owner_name", "email", "pincode")
