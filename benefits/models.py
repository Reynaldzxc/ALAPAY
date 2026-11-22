from django.db import models
from employees.models import Employee


class Allowance(models.Model):
    BENEFIT_TYPES = [
        ("Allowance", "Allowance"),
        ("Bonus", "Bonus"),
    ]

    FREQUENCIES = [
        ("One-time", "One-time"),
        ("Per Payroll", "Per Payroll"),
        ("Monthly", "Monthly"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="allowances",
    )

    name = models.CharField(max_length=100)

    benefit_type = models.CharField(
        max_length=20,
        choices=BENEFIT_TYPES,
        default="Allowance",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCIES,
        default="Per Payroll",
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["employee", "name"]

    def __str__(self):
        return f"{self.employee.employee_id} - {self.name}"


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ("Vacation", "Vacation Leave"),
        ("Sick", "Sick Leave"),
        ("Emergency", "Emergency Leave"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="leave_requests",
    )

    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES,
    )

    start_date = models.DateField()
    end_date = models.DateField()
    
    reason = models.TextField(blank=True)
    is_paid = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type}"


class LeaveBalance(models.Model):
    LEAVE_TYPES = [
        ("Vacation", "Vacation Leave"),
        ("Sick", "Sick Leave"),
        ("Emergency", "Emergency Leave"),
        ("Other", "Other"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="leave_balances",
    )

    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES,
    )

    year = models.PositiveIntegerField()

    allocated_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    used_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    class Meta:
        ordering = ["employee", "leave_type", "year"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "leave_type", "year"],
                name="unique_employee_leave_balance",
            )
        ]

    @property
    def remaining_days(self):
        return self.allocated_days - self.used_days

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type} ({self.year})"