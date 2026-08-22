from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StaffProfile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        prefix = "OWNER" if instance.is_owner else "STF"
        StaffProfile.objects.create(user=instance, staff_code=f"{prefix}{instance.pk:05d}")


@receiver(post_save, sender=StaffProfile)
def create_or_sync_staff_party(sender, instance, created, **kwargs):
    user = instance.user
    if user and user.user_type == User.UserType.STAFF:
        from parties.models import Party, PartyType

        staff_type, _ = PartyType.objects.get_or_create(name="Staff")

        party = Party.objects.filter(party_type=staff_type).filter(
            models.Q(phone_1=user.phone) | (models.Q(email=user.email) & ~models.Q(email="")) | models.Q(name=user.full_name)
        ).first()

        if not party:
            party = Party(
                name=user.full_name,
                party_type=staff_type,
                email=user.email or "",
                phone_1=user.phone or "",
                profile_picture=instance.profile_photo,
                manual_address=instance.notes or "",
            )
        else:
            party.name = user.full_name
            party.email = user.email or ""
            party.phone_1 = user.phone or ""
            if instance.profile_photo:
                party.profile_picture = instance.profile_photo
            if instance.notes:
                party.manual_address = instance.notes

        party.save()


@receiver(post_save, sender=User)
def sync_user_changes_to_staff_party(sender, instance, created, **kwargs):
    if not created and instance.user_type == User.UserType.STAFF:
        if hasattr(instance, "staff_profile"):
            create_or_sync_staff_party(sender=StaffProfile, instance=instance.staff_profile, created=False)
