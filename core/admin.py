from django.contrib import admin
from .models import Color, Company, Currency, SystemSettings
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