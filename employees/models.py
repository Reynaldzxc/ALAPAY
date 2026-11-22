from django.db import models

class Employee(models.Model):
    EMPLOYMENT_TYPES = [
        ("Regular", "Regular"),
        ("Contractual", "Contractual"),
        ("Part-time", "Part-time"),
    ]
    PAY_FREQUENCIES = [
        ("Monthly", "Monthly"),
        ("Weekly", "Weekly"),
        ("Daily", "Daily"),
    ]

    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    date_hired = models.DateField()
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    pay_frequency = models.CharField(
        max_length=10,
        choices=PAY_FREQUENCIES,
        default="Monthly",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_employee = Employee.objects.order_by("-id").first()

            if last_employee and last_employee.employee_id.startswith("EMP-"):
                last_number = int(last_employee.employee_id.split("-")[-1])
            else:
                last_number = 0

            self.employee_id = f"EMP-{last_number + 1:04d}"

        super().save(*args, **kwargs)
