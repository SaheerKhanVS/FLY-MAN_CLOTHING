from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StaffProfile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        prefix = "OWNER" if instance.is_owner else "STF"
        StaffProfile.objects.create(user=instance, staff_code=f"{prefix}{instance.pk:05d}")
