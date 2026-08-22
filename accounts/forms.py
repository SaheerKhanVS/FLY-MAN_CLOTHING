from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import StaffProfile, User


def validate_phone(value):
    if not value:
        raise ValidationError("Phone number is required.")
    cleaned = str(value).replace(" ", "").replace("-", "").replace("+", "").strip()
    if not cleaned.isdigit() or not (8 <= len(cleaned) <= 15):
        raise ValidationError("Enter a valid phone number with 8 to 15 digits.")
    return cleaned


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=True, error_messages={"required": "First name is required."})
    last_name = forms.CharField(required=True, error_messages={"required": "Last name is required."})
    phone = forms.CharField(required=True, error_messages={"required": "Phone number is required."})
    username = forms.CharField(required=False)
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Leave blank to keep current password"}),
        min_length=8,
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "email")

    def __init__(self, *args, **kwargs):
        self.is_owner = kwargs.pop("is_owner", False)
        super().__init__(*args, **kwargs)
        if self.is_owner:
            self.fields["username"] = forms.CharField(
                required=True,
                initial=self.instance.username if self.instance else ""
            )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if self.is_owner:
            if not username:
                raise ValidationError("Username is required.")
            qs = User.objects.filter(username__iexact=username)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("This username is already in use by another user.")
        return username

    def clean_phone(self):
        raw_phone = self.cleaned_data.get("phone", "")
        cleaned = validate_phone(raw_phone)
        qs = User.objects.filter(phone=cleaned)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This phone number is already registered to another user.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.is_owner:
            new_username = self.cleaned_data.get("username")
            if new_username:
                user.username = new_username
            new_password = self.cleaned_data.get("password")
            if new_password:
                user.set_password(new_password)
                user.raw_password = new_password
        if commit:
            user.save()
        return user


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
        raw_phone = self.cleaned_data.get("phone", "")
        cleaned = validate_phone(raw_phone)
        if User.objects.filter(phone=cleaned).exists():
            raise ValidationError("This phone number is already registered to another user.")
        return cleaned

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already in use.")
        return username


class StaffEditForm(forms.ModelForm):
    username = forms.CharField(required=True)
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Leave blank to keep current password"}),
        min_length=8
    )
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    phone = forms.CharField()

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "phone", "email", "is_active")

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise ValidationError("Username is required.")
        qs = User.objects.filter(username__iexact=username)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This username is already taken by another account.")
        return username

    def clean_phone(self):
        raw_phone = self.cleaned_data.get("phone", "")
        cleaned = validate_phone(raw_phone)
        qs = User.objects.filter(phone=cleaned)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This phone number is already registered to another user.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("username"):
            user.username = self.cleaned_data["username"]
        new_password = self.cleaned_data.get("password")
        if new_password:
            user.set_password(new_password)
            user.raw_password = new_password
        if commit:
            user.save()
        return user


class StaffDetailsForm(ProfileDetailsForm):
    joining_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    salary = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2)
    commission_enabled = forms.BooleanField(required=False)

    class Meta(ProfileDetailsForm.Meta):
        fields = ("joining_date", "salary", "commission_enabled", "profile_photo", "notes")

