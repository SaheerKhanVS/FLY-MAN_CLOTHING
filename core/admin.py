from django.contrib import admin
from .models import Color, Company, Currency, SystemSettings, ActionHistory, TrashItem
from django.utils.html import format_html

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
    
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("name",)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("color_preview","name", "hex_code","category",)
    search_fields = ( "name", "hex_code", "category",)
    list_filter = ("category", )
    ordering = ( "name", )
    list_per_page = 50
    def color_preview(self, obj):
        return format_html('<div style="width:25px; height:25px; border:1px solid #ccc; background:{};"></div>',obj.hex_code,)
    color_preview.short_description = "Color"


@admin.register(ActionHistory)
class ActionHistoryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user_name", "action", "action_type", "ip_address")
    search_fields = ("user_name", "action", "details", "ip_address")
    list_filter = ("action_type", "created_at")
    ordering = ("-created_at",)


@admin.register(TrashItem)
class TrashItemAdmin(admin.ModelAdmin):
    list_display = ("deleted_at", "title", "item_type", "deleted_by_name")
    search_fields = ("title", "deleted_by_name")
    list_filter = ("item_type", "deleted_at")
    ordering = ("-deleted_at",)