from django.db import models
from employees.models import Employee




class PayrollPeriod(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Processing", "Processing"),
        ("Completed", "Completed"),
    ]

    FREQUENCY_CHOICES = [
        ("Monthly", "Monthly"),
        ("Weekly", "Weekly"),
        ("Daily", "Daily"),
    ]

    name = models.CharField(max_length=100)
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default="Monthly",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Draft",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["start_date", "end_date", "frequency"],
                name="unique_payroll_period_dates_frequency",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.frequency}: {self.start_date} - {self.end_date})"



class DeductionRule(models.Model):
    CALCULATION_TYPES = [
        ("Percentage", "Percentage"),
        ("Fixed", "Fixed Amount"),
    ]

    CALCULATION_BASES = [
        ("Basic Pay", "Basic Pay"),
        ("Gross Pay", "Gross Pay"),
    ]

    name = models.CharField(max_length=100, unique=True)
    calculation_type = models.CharField(
        max_length=20,
        choices=CALCULATION_TYPES,
    )
    calculation_basis = models.CharField(
        max_length=20,
        choices=CALCULATION_BASES,
        default="Gross Pay",
    )
    employee_rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )
    employer_rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class OvertimeRule(models.Model):
    name = models.CharField(max_length=100, unique=True)
    multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
    )
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.multiplier}x)"


class PayrollRecord(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Processed", "Processed"),
        ("Approved", "Approved"),
        ("Paid", "Paid"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="payroll_records",
    )

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.PROTECT,
        related_name="payroll_records",
    )

    basic_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    overtime_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    allowances = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    gross_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    net_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total_working_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )

    total_overtime_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Draft",
    )

    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "payroll_period"],
                name="unique_employee_payroll_period",
            )
        ]

    def __str__(self):
        return f"{self.employee.employee_id} - {self.payroll_period.name}"


class PayrollItem(models.Model):
    ITEM_TYPES = [
        ("Earning", "Earning"),
        ("Deduction", "Deduction"),
    ]

    payroll_record = models.ForeignKey(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="items",
    )

    description = models.CharField(max_length=150)

    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPES,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["item_type", "description"]

    def __str__(self):
        return f"{self.description} - {self.amount}"


class PayrollSettings(models.Model):
    standard_hours_per_day = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    weekly_working_days = models.PositiveSmallIntegerField()

    monthly_working_days = models.PositiveSmallIntegerField()

    effective_date = models.DateField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_date"]
        verbose_name_plural = "Payroll Settings"

    def __str__(self):
        return f"Payroll Settings - {self.effective_date}"


class SSSContributionBracket(models.Model):
    minimum_compensation = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    maximum_compensation = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    monthly_salary_credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    employee_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    employer_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    employee_mpf_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    employer_mpf_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    employer_ec_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["minimum_compensation"]
        constraints = [
            models.UniqueConstraint(
                fields=["minimum_compensation", "effective_date"],
                name="unique_sss_bracket_effective_date",
            )
        ]

    def __str__(self):
        return f"SSS Bracket - {self.minimum_compensation}"


class StatutoryContributionRule(models.Model):
    CONTRIBUTION_TYPES = [
        ("PhilHealth", "PhilHealth"),
        ("Pag-IBIG", "Pag-IBIG"),
    ]

    name = models.CharField(max_length=50, choices=CONTRIBUTION_TYPES)
    employee_rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )
    employer_rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )
    minimum_monthly_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    maximum_monthly_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    maximum_contribution_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "-effective_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "minimum_monthly_salary", "effective_date"],
                name="unique_statutory_rule_effective_date",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.effective_date}"


class WithholdingTaxBracket(models.Model):
    PAY_FREQUENCIES = [
        ("Daily", "Daily"),
        ("Weekly", "Weekly"),
        ("Semi-monthly", "Semi-monthly"),
        ("Monthly", "Monthly"),
    ]

    pay_frequency = models.CharField(
        max_length=20,
        choices=PAY_FREQUENCIES,
    )
    minimum_taxable_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    maximum_taxable_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    base_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    tax_rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["pay_frequency", "minimum_taxable_income"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "pay_frequency",
                    "minimum_taxable_income",
                    "effective_date",
                ],
                name="unique_tax_bracket_effective_date",
            )
        ]

    def __str__(self):
        return (
            f"{self.pay_frequency} Tax Bracket - "
            f"{self.minimum_taxable_income}"
        )


class EmployerContribution(models.Model):
    payroll_record = models.OneToOneField(
        PayrollRecord,
        on_delete=models.CASCADE,
        related_name="employer_contributions",
    )
    sss_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    sss_mpf_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    sss_ec_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    philhealth_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    pagibig_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    total_employer_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Employer Contributions - {self.payroll_record}"