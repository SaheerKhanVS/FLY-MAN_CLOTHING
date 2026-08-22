import hashlib
from django.db import models


class PartyType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Party(models.Model):
    name = models.CharField(max_length=150, db_index=True, verbose_name="Party Name")
    party_type = models.ForeignKey(
        PartyType, on_delete=models.PROTECT, related_name="parties", verbose_name="Party Type"
    )
    email = models.EmailField(blank=True, verbose_name="E-mail")
    phone_1 = models.CharField(max_length=20, blank=True, verbose_name="Phone Number 1")
    phone_2 = models.CharField(max_length=20, blank=True, verbose_name="Phone Number 2")
    pincode = models.CharField(max_length=10, blank=True, verbose_name="Pincode")
    locality = models.CharField(max_length=100, blank=True, verbose_name="Locality")
    district = models.CharField(max_length=100, blank=True, verbose_name="District")
    state = models.CharField(max_length=100, blank=True, verbose_name="State")
    manual_address = models.TextField(blank=True, verbose_name="Manual Address")
    company_name = models.CharField(max_length=150, blank=True, verbose_name="Party Company Name")
    owner_name = models.CharField(max_length=150, blank=True, verbose_name="Party Owner Name")
    profile_picture = models.ImageField(upload_to="parties/photos/", blank=True, null=True, verbose_name="Profile Picture")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Balance")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Parties"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["name"]),
        ]


    def __str__(self):
        return f"{self.name} ({self.party_type.name})"

    @property
    def avatar_initial(self):
        if self.name and self.name.strip():
            return self.name.strip()[0].upper()
        return "P"

    @property
    def avatar_bg_color(self):
        colors = [
            "#7c5cff", "#00d4c8", "#ff4757", "#2ed573",
            "#ffa502", "#1e90ff", "#ff6b81", "#70a1ff",
            "#e84393", "#00cec9", "#fdcb6e", "#6c5ce7"
        ]
        val = int(hashlib.md5(self.name.encode("utf-8")).hexdigest(), 16)
        return colors[val % len(colors)]
