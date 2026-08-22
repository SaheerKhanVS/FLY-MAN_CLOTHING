from django import forms
from django.core.exceptions import ValidationError
from .models import Party, PartyType


class PartyTypeForm(forms.ModelForm):
    class Meta:
        model = PartyType
        fields = ("name",)

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Party type name is required.")
        if PartyType.objects.filter(name__iexact=name).exists():
            raise ValidationError("This party type already exists.")
        return name


class PartyForm(forms.ModelForm):
    name = forms.CharField(required=True, error_messages={"required": "Party Name is required."})
    party_type = forms.ModelChoiceField(
        queryset=PartyType.objects.all(),
        required=True,
        empty_label="-- Select Party Type --",
        error_messages={"required": "Party Type is required."}
    )

    class Meta:
        model = Party
        fields = (
            "name",
            "party_type",
            "email",
            "phone_1",
            "phone_2",
            "pincode",
            "locality",
            "district",
            "state",
            "manual_address",
            "company_name",
            "owner_name",
            "profile_picture",
            "balance",
        )

    def clean_profile_picture(self):
        image = self.cleaned_data.get("profile_picture")
        if image and hasattr(image, "content_type"):
            if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise ValidationError("Only JPG, PNG, and WEBP images are allowed.")
            if image.size > 2 * 1024 * 1024:
                raise ValidationError("Profile picture must be 2 MB or smaller.")
        return image
