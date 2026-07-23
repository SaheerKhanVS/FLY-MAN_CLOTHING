from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import StaffProfile, User


@admin.register(User)
class FlymenUserAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "phone", "user_type", "is_active", "is_staff")
    list_filter = ("user_type", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "phone", "email")
    fieldsets = UserAdmin.fieldsets + (("Flymen", {"fields": ("phone", "user_type", "created_at", "updated_at")}),)
    readonly_fields = ("created_at", "updated_at")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("staff_code", "user", "joining_date", "salary", "commission_enabled")
    list_filter = ("commission_enabled", "joining_date")
    search_fields = ("staff_code", "user__username", "user__first_name", "user__phone")
    list_select_related = ("user",)
