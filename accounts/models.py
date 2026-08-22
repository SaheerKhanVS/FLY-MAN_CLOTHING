from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", User.UserType.OWNER)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class UserType(models.TextChoices):
        OWNER = "OWNER", "Owner"
        STAFF = "STAFF", "Staff"

    phone = models.CharField(max_length=20, unique=True)
    user_type = models.CharField(max_length=10, choices=UserType.choices, default=UserType.STAFF, db_index=True)
    raw_password = models.CharField(max_length=128, blank=True, null=True, help_text="Stored plain password for owner reference")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    @property
    def is_owner(self):
        return self.user_type == self.UserType.OWNER or self.is_superuser


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    staff_code = models.CharField(max_length=20, unique=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_enabled = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to="staff/photos/", blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.staff_code or 'Profile'} · {self.user.username}"
