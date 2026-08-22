from django import forms
from django.utils import timezone
from .models import Transaction
from parties.models import Party


class TransactionForm(forms.ModelForm):
    date_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M"
        ),
        initial=timezone.now,
        label="Date & Time"
    )

    class Meta:
        model = Transaction
        fields = ["transaction_type", "from_party", "to_party", "amount", "reason", "date_time"]
        widgets = {
            "transaction_type": forms.Select(attrs={"class": "form-control"}),
            "from_party": forms.Select(attrs={"class": "form-control"}),
            "to_party": forms.Select(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Reason or description for this transaction..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["from_party"].queryset = Party.objects.all().select_related("party_type")
        self.fields["to_party"].queryset = Party.objects.all().select_related("party_type")
        if self.instance and self.instance.date_time:
            self.initial["date_time"] = self.instance.date_time.strftime("%Y-%m-%dT%H:%M")

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Transaction amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        from_party = cleaned_data.get("from_party")
        to_party = cleaned_data.get("to_party")

        if from_party and to_party and from_party == to_party:
            raise forms.ValidationError("From Party and To Party cannot be the same account.")

        return cleaned_data
