from django import forms
from django.core.exceptions import ValidationError
from .models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "company_name",
            "owner_name",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "gst_number",
            "logo",
        ]

    def clean_company_name(self):
        company_name = self.cleaned_data.get("company_name")
        if len(company_name.strip()) < 3:
            raise ValidationError("Company name must be at least 3 characters.")
        return company_name

    def clean_owner_name(self):
        owner_name = self.cleaned_data.get("owner_name")
        if len(owner_name.strip()) < 3:
            raise ValidationError("Owner name must be at least 3 characters.")
        return owner_name

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        phone = phone.replace(" ", "")
        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if len(phone) != 10:
            raise ValidationError("Phone number must be exactly 10 digits.")
        return phone

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get("postal_code")
        if not postal_code.isdigit():
            raise ValidationError("Postal code must contain only digits.")
        if len(postal_code) != 6:
            raise ValidationError("Postal code must be exactly 6 digits.")
        return postal_code

    def clean_gst_number(self):
        gst_number = self.cleaned_data.get("gst_number")
        if gst_number:
            gst_number = gst_number.upper()
            if len(gst_number) != 15:
                raise ValidationError("GST Number must be 15 characters.")
        return gst_number

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if not logo:return logo
        if hasattr(logo, "content_type"):
            allowed_types = ["image/jpeg","image/png","image/webp",]
            if logo.content_type not in allowed_types:raise forms.ValidationError("Only JPG, PNG and WEBP files are allowed.")
            if logo.size > 2 * 1024 * 1024:raise forms.ValidationError("Image size must be less than 2MB.")
        return logo
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        if email:
            email = email.lower()
        return cleaned_data
