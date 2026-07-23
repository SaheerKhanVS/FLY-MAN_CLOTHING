from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import StaffProfile, User


def validate_phone(value):
    digits = value.replace(" ", "").replace("-", "")
    if not digits.isdigit() or not 8 <= len(digits) <= 15:
        raise ValidationError("Enter a valid phone number with 8 to 15 digits.")
    return digits


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    phone = forms.CharField(validators=[validate_phone])

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "email")


class ProfileDetailsForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ("profile_photo", "notes")

    def clean_profile_photo(self):
        image = self.cleaned_data.get("profile_photo")
        if image and hasattr(image, "content_type"):
            if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise ValidationError("Only JPG, PNG, and WEBP images are allowed.")
            if image.size > 2 * 1024 * 1024:
                raise ValidationError("Profile photo must be 2 MB or smaller.")
        return image


class StaffCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    joining_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    salary = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2)
    commission_enabled = forms.BooleanField(required=False)
    profile_photo = forms.ImageField(required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = User
        fields = ("username", "password", "first_name", "last_name", "phone", "email")

    def clean_phone(self):
        return validate_phone(self.cleaned_data["phone"])

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already in use.")
        return username


class StaffEditForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    phone = forms.CharField(validators=[validate_phone])
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "email", "is_active")

    def clean_phone(self):
        return validate_phone(self.cleaned_data["phone"])


class StaffDetailsForm(ProfileDetailsForm):
    joining_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    salary = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2)
    commission_enabled = forms.BooleanField(required=False)

    class Meta(ProfileDetailsForm.Meta):
        fields = ("joining_date", "salary", "commission_enabled", "profile_photo", "notes")
