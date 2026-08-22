from django.conf import settings
from django.db import models
from django.utils import timezone

from parties.models import Party


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ("receipt", "Receipt (Money In)"),
        ("payment", "Payment (Money Out)"),
    ]

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default="receipt",
        db_index=True,
        verbose_name="Transaction Type"
    )
    from_party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="outgoing_transactions",
        verbose_name="From Party"
    )
    to_party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="incoming_transactions",
        verbose_name="To Party"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount (₹)"
    )
    reason = models.TextField(
        blank=True,
        verbose_name="Reason / Notes"
    )
    date_time = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Date & Time"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_transactions"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_time", "-created_at"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [
            models.Index(fields=["-date_time", "-created_at"]),
            models.Index(fields=["transaction_type"]),
        ]


    def __str__(self):
        return f"{self.get_transaction_type_display()} #{self.id} - ₹{self.amount} ({self.from_party.name} ➔ {self.to_party.name})"
