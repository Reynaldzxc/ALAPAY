from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "first_name",
            "last_name",
            "position",
            "department",
            "employment_type",
            "contact_number",
            "email",
            "date_hired",
            "basic_salary",
            "is_active",
        ]

        widgets = {
            "date_hired": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "basic_salary": forms.NumberInput(
                attrs={
                    "step": "0.01",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "form-control",
                }
            )
