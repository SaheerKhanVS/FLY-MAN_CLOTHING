from django.conf import settings
from django.db import models


class Company(models.Model):
    company_name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_companies"
    )
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    logo = models.ImageField(upload_to="company/logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.company_name

    @property
    def owner_name(self):
        return self.owner.full_name if self.owner else "—"


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Color(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hex_code = models.CharField(max_length=7)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class SystemSettings(models.Model):
    FONT_SIZE_CHOICES = [
        ("small", "Small"),
        ("medium", "Medium (Default)"),
        ("large", "Large"),
        ("xlarge", "Extra Large"),
    ]

    OBJECT_SIZE_CHOICES = [
        ("small", "Small (Compact)"),
        ("medium", "Medium (Default)"),
        ("large", "Large"),
        ("xlarge", "Extra Large"),
    ]

    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="settings")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    financial_year_start = models.DateField()
    financial_year_end = models.DateField()
    allow_negative_balance = models.BooleanField(default=False)
    default_commission = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    primary_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_settings")
    secondary_color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name="secondary_settings")
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default="small")
    object_size = models.CharField(max_length=10, choices=OBJECT_SIZE_CHOICES, default="small")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"{self.company.company_name} Settings"


class ActionHistory(models.Model):
    ACTION_TYPE_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("SYSTEM", "System"),
        ("CLEAR", "Clear"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="action_histories"
    )
    user_name = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, default="SYSTEM", db_index=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Action History"
        verbose_name_plural = "Action Histories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["action_type"]),
        ]


    def __str__(self):
        return f"[{self.get_action_type_display()}] {self.action} by {self.user_name or 'System'} at {self.created_at}"

    @classmethod
    def trim_old_records(cls):
        """
        Auto-delete oldest 10 records if total count exceeds 100.
        """
        count = cls.objects.count()
        if count > 100:
            oldest_ids = list(cls.objects.order_by("created_at").values_list("id", flat=True)[:10])
            if oldest_ids:
                cls.objects.filter(id__in=oldest_ids).delete()


class TrashItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ("PARTY", "Party"),
        ("TRANSACTION", "Transaction"),
        ("STAFF", "Staff Member"),
    ]

    item_type = models.CharField(max_length=50, choices=ITEM_TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_trash_items"
    )
    deleted_by_name = models.CharField(max_length=255, blank=True)
    serialized_data = models.JSONField()
    deleted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Trash Item"
        verbose_name_plural = "Trash Items"
        ordering = ["-deleted_at"]
        indexes = [
            models.Index(fields=["-deleted_at"]),
            models.Index(fields=["item_type"]),
        ]

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.title} (Deleted at {self.deleted_at})"


