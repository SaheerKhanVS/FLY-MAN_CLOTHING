from django import forms
from django.core.exceptions import ValidationError
from django.forms import Select
from accounts.models import User
from .models import Color, Company, SystemSettings


class CompanyForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="Select Owner Account",
    )

    class Meta:
        model = Company
        fields = [
            "company_name",
            "owner",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        owners = User.objects.filter(user_type=User.UserType.OWNER)
        if owners.exists():
            self.fields["owner"].queryset = owners
        else:
            self.fields["owner"].queryset = User.objects.all()

    def clean_company_name(self):
        company_name = self.cleaned_data.get("company_name")
        if len(company_name.strip()) < 3:
            raise ValidationError("Company name must be at least 3 characters.")
        return company_name

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
        if not logo:
            return logo
        if hasattr(logo, "content_type"):
            allowed_types = ["image/jpeg", "image/png", "image/webp"]
            if logo.content_type not in allowed_types:
                raise forms.ValidationError("Only JPG, PNG and WEBP files are allowed.")
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image size must be less than 2MB.")
        return logo

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        if email:
            email = email.lower()
        return cleaned_data


class AjaxColorSelect(Select):
    """
    A Select widget that never dumps the whole Color table into the page.
    """
    def __init__(self, attrs=None):
        base_attrs = {"class": "color-select"}
        if attrs:
            base_attrs.update(attrs)
        super().__init__(attrs=base_attrs, choices=())

    def get_context(self, name, value, attrs):
        self.choices = [("", "---------")]
        color = self._get_color(value)
        if color:
            self.choices.append((color.id, color.name))
        return super().get_context(name, value, attrs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        color = self._get_color(value)
        if color:
            option["attrs"]["data-color"] = color.hex_code
            option["attrs"]["data-category"] = color.category
        return option

    @staticmethod
    def _get_color(value):
        if not value:
            return None
        try:
            return Color.objects.only("id", "name", "hex_code", "category").get(pk=value)
        except (Color.DoesNotExist, ValueError, TypeError):
            return None


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            "currency",
            "financial_year_start",
            "financial_year_end",
            "allow_negative_balance",
            "default_commission",
            "primary_color",
            "secondary_color",
            "font_size",
            "object_size",
        ]
        widgets = {
            "financial_year_start": forms.DateInput(attrs={"type": "date"}),
            "financial_year_end": forms.DateInput(attrs={"type": "date"}),
            "font_size": forms.Select(attrs={"class": "size-select", "data-preview": "font-size"}),
            "object_size": forms.Select(attrs={"class": "size-select", "data-preview": "object-size"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["currency"].widget.attrs.update({"class": "tom-select"})
        self.fields["primary_color"].widget = AjaxColorSelect()
        self.fields["secondary_color"].widget = AjaxColorSelect()