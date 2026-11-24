from django import forms
from .models import LeaveRequest, Allowance


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest

        fields = [
            "employee",
            "leave_type",
            "start_date",
            "end_date",
            "reason",
            "is_paid",
        ]

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 3}),
        }


class AllowanceForm(forms.ModelForm):
    class Meta:
        model = Allowance

        fields = [
            "employee",
            "name",
            "benefit_type",
            "amount",
            "frequency",
            "start_date",
            "end_date",
            "is_taxable",
            "is_active",
        ]

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
