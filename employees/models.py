from django.db import models


from django.db import models


class Employee(models.Model):
    EMPLOYMENT_TYPES = [
        ("Regular", "Regular"),
        ("Contractual", "Contractual"),
        ("Part-time", "Part-time"),
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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"
