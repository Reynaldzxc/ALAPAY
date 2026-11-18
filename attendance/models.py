from django.db import models
from employees.models import Employee


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Late", "Late"),
        ("Half-day", "Half-day"),
        ("On Leave", "On Leave"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="attendance_records"
    )

    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Present")

    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("employee", "date")
        ordering = ["-date", "employee__employee_id"]

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date}"
