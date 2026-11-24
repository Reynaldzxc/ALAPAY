from django import forms
from .models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = [
            "employee",
            "date",
            "time_in",
            "time_out",
            "status",
            "remarks",
        ]

        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "time_in": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),
            "time_out": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "rows": 3,
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

    def clean(self):
        cleaned_data = super().clean()

        time_in = cleaned_data.get("time_in")
        time_out = cleaned_data.get("time_out")
        status = cleaned_data.get("status")

        if status in ["Present", "Late", "Half-day"]:
            if not time_in or not time_out:
                raise forms.ValidationError(
                    "Time In and Time Out are required for this attendance status."
                )

        return cleaned_data
