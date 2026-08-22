from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "transaction_type", "from_party", "to_party", "amount", "date_time", "created_by"]
    list_filter = ["transaction_type", "date_time"]
    search_fields = ["from_party__name", "to_party__name", "reason"]
    date_hierarchy = "date_time"
