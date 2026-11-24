import calendar
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import models, transaction
from django.utils import timezone

from attendance.models import Attendance
from benefits.models import Allowance, LeaveRequest
from employees.models import Employee
from .models import (
    PayrollSettings,
    OvertimeRule,
    DeductionRule,
    PayrollRecord,
    PayrollItem,
    SSSContributionBracket,
    StatutoryContributionRule,
    WithholdingTaxBracket,
    EmployerContribution,
)

ZERO = Decimal("0.00")
ONE_HUNDRED = Decimal("100")


def money(value):
    return Decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def get_payroll_settings(payroll_period):
    settings = (
        PayrollSettings.objects.filter(
            is_active=True,
            effective_date__lte=payroll_period.start_date,
        )
        .order_by("-effective_date")
        .first()
    )

    if settings is None:
        raise ValueError("No active payroll settings found for this period.")

    return settings


def get_monthly_equivalent_salary(employee, settings):
    if employee.pay_frequency == "Monthly":
        salary = employee.basic_salary

    elif employee.pay_frequency == "Weekly":
        salary = employee.basic_salary * Decimal("52") / Decimal("12")

    elif employee.pay_frequency == "Daily":
        salary = employee.basic_salary * Decimal(settings.monthly_working_days)

    else:
        raise ValueError("Invalid employee pay frequency.")

    return money(salary)


def get_monthly_contribution_factor(employee, payroll_period):
    if employee.pay_frequency == "Monthly":
        if payroll_period.end_date.day <= 15:
            return Decimal("0.50")

        if payroll_period.start_date.day >= 16:
            return Decimal("0.50")

        raise ValueError(
            "Monthly payroll periods must follow the 1st–15th "
            "and 16th–last-day cutoff schedule."
        )

    if employee.pay_frequency not in ("Weekly", "Daily"):
        raise ValueError("Invalid employee pay frequency.")

    factor = Decimal("0")
    current_month = payroll_period.start_date.replace(day=1)

    while current_month <= payroll_period.end_date:
        last_day = calendar.monthrange(
            current_month.year,
            current_month.month,
        )[1]

        month_end = current_month.replace(day=last_day)

        if payroll_period.start_date <= month_end <= payroll_period.end_date:
            factor += Decimal("1")

        if current_month.month == 12:
            current_month = current_month.replace(
                year=current_month.year + 1,
                month=1,
            )
        else:
            current_month = current_month.replace(month=current_month.month + 1)

    return factor


def calculate_basic_pay(employee, payroll_period):
    settings = get_payroll_settings(payroll_period)

    hours_per_day = settings.standard_hours_per_day

    if hours_per_day <= 0:
        raise ValueError("Standard hours per day must be greater than zero.")

    if employee.pay_frequency == "Monthly":
        working_days = settings.monthly_working_days
    elif employee.pay_frequency == "Weekly":
        working_days = settings.weekly_working_days
    elif employee.pay_frequency == "Daily":
        working_days = 1
    else:
        raise ValueError("Invalid employee pay frequency.")

    if working_days <= 0:
        raise ValueError("Configured working days must be greater than zero.")

    hourly_rate = employee.basic_salary / Decimal(working_days) / hours_per_day

    attendance_totals = Attendance.objects.filter(
        employee=employee,
        date__range=(
            payroll_period.start_date,
            payroll_period.end_date,
        ),
    ).aggregate(
        total_working_hours=models.Sum("working_hours"),
        total_overtime_hours=models.Sum("overtime_hours"),
    )

    total_hours = attendance_totals["total_working_hours"] or ZERO
    overtime_hours = attendance_totals["total_overtime_hours"] or ZERO

    regular_hours = total_hours - overtime_hours

    if regular_hours < 0:
        raise ValueError("Overtime hours cannot exceed total working hours.")

    if employee.pay_frequency == "Monthly":
        basic_pay = employee.basic_salary / Decimal("2")
    else:
        basic_pay = hourly_rate * regular_hours

    return {
        "basic_pay": money(basic_pay),
        "hourly_rate": money(hourly_rate),
        "regular_hours": regular_hours,
        "overtime_hours": overtime_hours,
    }


def calculate_overtime_pay(employee, payroll_period):
    settings = get_payroll_settings(payroll_period)

    if settings.standard_hours_per_day <= 0:
        raise ValueError("Standard hours per day must be greater than zero.")

    if employee.pay_frequency == "Monthly":
        working_days = settings.monthly_working_days
    elif employee.pay_frequency == "Weekly":
        working_days = settings.weekly_working_days
    elif employee.pay_frequency == "Daily":
        working_days = 1
    else:
        raise ValueError("Invalid employee pay frequency.")

    if working_days <= 0:
        raise ValueError("Configured working days must be greater than zero.")

    hourly_rate = (
        employee.basic_salary / Decimal(working_days) / settings.standard_hours_per_day
    )

    overtime_rule = (
        OvertimeRule.objects.filter(
            is_active=True,
            effective_date__lte=payroll_period.start_date,
        )
        .order_by("-effective_date")
        .first()
    )

    if overtime_rule is None:
        raise ValueError("No active overtime rule found for this period.")

    overtime_hours = (
        Attendance.objects.filter(
            employee=employee,
            date__range=(
                payroll_period.start_date,
                payroll_period.end_date,
            ),
        ).aggregate(total=models.Sum("overtime_hours"))["total"]
        or ZERO
    )

    overtime_pay = hourly_rate * overtime_hours * overtime_rule.multiplier

    return {
        "overtime_pay": money(overtime_pay),
        "overtime_hours": overtime_hours,
        "hourly_rate": money(hourly_rate),
        "multiplier": overtime_rule.multiplier,
    }


def calculate_allowances(employee, payroll_period):
    allowances = Allowance.objects.filter(
        employee=employee,
        is_active=True,
        start_date__lte=payroll_period.end_date,
    ).filter(
        models.Q(end_date__isnull=True)
        | models.Q(end_date__gte=payroll_period.start_date)
    )

    total_allowances = ZERO
    taxable_allowances = ZERO
    allowance_items = []

    for allowance in allowances:
        if allowance.frequency == "One-time":
            if not (
                payroll_period.start_date
                <= allowance.start_date
                <= payroll_period.end_date
            ):
                continue

            amount = allowance.amount

        elif allowance.frequency == "Monthly":
            amount = allowance.amount / Decimal("2")

        else:
            amount = allowance.amount

        amount = money(amount)

        if amount > 0:
            total_allowances += amount

            allowance_items.append(
                {
                    "allowance": allowance,
                    "amount": amount,
                }
            )

            if allowance.is_taxable:
                taxable_allowances += amount

    return {
        "allowances": money(total_allowances),
        "taxable_allowances": money(taxable_allowances),
        "non_taxable_allowances": money(total_allowances - taxable_allowances),
        "allowance_items": allowance_items,
    }


def calculate_gross_pay(employee, payroll_period):
    basic = calculate_basic_pay(employee, payroll_period)
    overtime = calculate_overtime_pay(employee, payroll_period)
    allowance = calculate_allowances(employee, payroll_period)

    gross_pay = basic["basic_pay"] + overtime["overtime_pay"] + allowance["allowances"]

    return {
        "basic_pay": basic["basic_pay"],
        "overtime_pay": overtime["overtime_pay"],
        "allowances": allowance["allowances"],
        "taxable_allowances": allowance["taxable_allowances"],
        "non_taxable_allowances": allowance["non_taxable_allowances"],
        "gross_pay": money(gross_pay),
    }


def calculate_absence_deduction(employee, payroll_period):
    if employee.pay_frequency != "Monthly":
        return {
            "deduction_items": [],
            "total_deduction": ZERO,
        }

    settings = get_payroll_settings(payroll_period)

    if settings.monthly_working_days <= 0:
        raise ValueError("Monthly working days must be greater than zero.")

    daily_rate = employee.basic_salary / Decimal(settings.monthly_working_days)

    paid_leave_dates = set()
    unpaid_leave_dates = set()

    paid_leaves = LeaveRequest.objects.filter(
        employee=employee,
        status="Approved",
        is_paid=True,
        start_date__lte=payroll_period.end_date,
        end_date__gte=payroll_period.start_date,
    )

    unpaid_leaves = LeaveRequest.objects.filter(
        employee=employee,
        status="Approved",
        is_paid=False,
        start_date__lte=payroll_period.end_date,
        end_date__gte=payroll_period.start_date,
    )

    for leave in paid_leaves:
        current_date = max(leave.start_date, payroll_period.start_date)
        last_date = min(leave.end_date, payroll_period.end_date)

        while current_date <= last_date:
            if current_date.weekday() < 5:
                paid_leave_dates.add(current_date)
            current_date += timedelta(days=1)

    for leave in unpaid_leaves:
        current_date = max(leave.start_date, payroll_period.start_date)
        last_date = min(leave.end_date, payroll_period.end_date)

        while current_date <= last_date:
            if current_date.weekday() < 5:
                unpaid_leave_dates.add(current_date)
            current_date += timedelta(days=1)

    deduction_days = {}

    attendance_records = Attendance.objects.filter(
        employee=employee,
        date__range=(
            payroll_period.start_date,
            payroll_period.end_date,
        ),
    )

    for attendance in attendance_records:
        if attendance.date.weekday() >= 5 or attendance.date in paid_leave_dates:
            continue

        if attendance.status == "Absent":
            deduction_days[attendance.date] = (
                "Absence",
                Decimal("1.00"),
            )

        elif attendance.status == "Half-day":
            deduction_days[attendance.date] = (
                "Half-day Absence",
                Decimal("0.50"),
            )

    for leave_date in unpaid_leave_dates:
        if leave_date not in paid_leave_dates:
            deduction_days[leave_date] = (
                "Unpaid Leave",
                Decimal("1.00"),
            )

    absence_days = sum(
        (days for category, days in deduction_days.values() if category == "Absence"),
        ZERO,
    )

    half_days = sum(
        (
            days
            for category, days in deduction_days.values()
            if category == "Half-day Absence"
        ),
        ZERO,
    )

    unpaid_days = sum(
        (
            days
            for category, days in deduction_days.values()
            if category == "Unpaid Leave"
        ),
        ZERO,
    )

    deduction_items = []

    for description, days in [
        ("Absence Deduction", absence_days),
        ("Half-day Absence Deduction", half_days),
        ("Unpaid Leave Deduction", unpaid_days),
    ]:
        if days > 0:
            amount = money(daily_rate * days)

            deduction_items.append(
                {
                    "name": description,
                    "amount": amount,
                    "days": days,
                }
            )

    total_deduction = sum(
        (item["amount"] for item in deduction_items),
        ZERO,
    )

    return {
        "deduction_items": deduction_items,
        "total_deduction": money(total_deduction),
    }


def calculate_sss_contribution(monthly_salary, payroll_period, factor):
    if factor <= 0:
        return {
            "employee": ZERO,
            "employer": ZERO,
            "mpf_employee": ZERO,
            "mpf_employer": ZERO,
            "ec": ZERO,
        }

    bracket = (
        SSSContributionBracket.objects.filter(
            is_active=True,
            effective_date__lte=payroll_period.start_date,
            minimum_compensation__lte=monthly_salary,
        )
        .filter(
            models.Q(maximum_compensation__isnull=True)
            | models.Q(maximum_compensation__gte=monthly_salary)
        )
        .order_by("-effective_date", "-minimum_compensation")
        .first()
    )

    if bracket is None:
        raise ValueError(
            f"No active SSS contribution bracket found for "
            f"monthly salary of {monthly_salary}."
        )

    return {
        "employee": money(bracket.employee_contribution * factor),
        "employer": money(bracket.employer_contribution * factor),
        "mpf_employee": money(bracket.employee_mpf_contribution * factor),
        "mpf_employer": money(bracket.employer_mpf_contribution * factor),
        "ec": money(bracket.employer_ec_contribution * factor),
    }


def calculate_statutory_rule(name, monthly_salary, payroll_period):
    rules = StatutoryContributionRule.objects.filter(
        name=name,
        is_active=True,
        effective_date__lte=payroll_period.start_date,
    ).order_by("-effective_date", "minimum_monthly_salary")

    if name == "Pag-IBIG":
        rule = (
            rules.filter(
                minimum_monthly_salary__lte=monthly_salary,
            )
            .filter(
                models.Q(maximum_monthly_salary__isnull=True)
                | models.Q(maximum_monthly_salary__gte=monthly_salary)
            )
            .first()
        )
    else:
        rule = rules.first()

    if rule is None:
        raise ValueError(f"No active {name} contribution rule found for this period.")

    contribution_salary = monthly_salary

    if rule.minimum_monthly_salary > contribution_salary:
        contribution_salary = rule.minimum_monthly_salary

    if (
        rule.maximum_monthly_salary is not None
        and contribution_salary > rule.maximum_monthly_salary
    ):
        contribution_salary = rule.maximum_monthly_salary

    if (
        rule.maximum_contribution_salary is not None
        and contribution_salary > rule.maximum_contribution_salary
    ):
        contribution_salary = rule.maximum_contribution_salary

    employee_amount = contribution_salary * rule.employee_rate / ONE_HUNDRED

    employer_amount = contribution_salary * rule.employer_rate / ONE_HUNDRED

    return {
        "employee": money(employee_amount),
        "employer": money(employer_amount),
    }


def calculate_statutory_contributions(employee, payroll_period):
    settings = get_payroll_settings(payroll_period)
    monthly_salary = get_monthly_equivalent_salary(employee, settings)
    factor = get_monthly_contribution_factor(employee, payroll_period)

    if factor <= 0:
        return {
            "employee_deductions": [],
            "total_employee": ZERO,
            "employer": {
                "sss": ZERO,
                "sss_mpf": ZERO,
                "sss_ec": ZERO,
                "philhealth": ZERO,
                "pagibig": ZERO,
                "total": ZERO,
            },
        }

    sss = calculate_sss_contribution(
        monthly_salary,
        payroll_period,
        factor,
    )

    philhealth_monthly = calculate_statutory_rule(
        "PhilHealth",
        monthly_salary,
        payroll_period,
    )

    pagibig_monthly = calculate_statutory_rule(
        "Pag-IBIG",
        monthly_salary,
        payroll_period,
    )

    philhealth_employee = money(philhealth_monthly["employee"] * factor)
    philhealth_employer = money(philhealth_monthly["employer"] * factor)

    pagibig_employee = money(pagibig_monthly["employee"] * factor)
    pagibig_employer = money(pagibig_monthly["employer"] * factor)

    employee_deductions = []

    sss_total = money(sss["employee"] + sss["mpf_employee"])

    if sss_total > 0:
        employee_deductions.append(
            {
                "name": "SSS Contribution",
                "amount": sss_total,
            }
        )

    if philhealth_employee > 0:
        employee_deductions.append(
            {
                "name": "PhilHealth Contribution",
                "amount": philhealth_employee,
            }
        )

    if pagibig_employee > 0:
        employee_deductions.append(
            {
                "name": "Pag-IBIG Contribution",
                "amount": pagibig_employee,
            }
        )

    total_employee = sum(
        (item["amount"] for item in employee_deductions),
        ZERO,
    )

    employer = {
        "sss": sss["employer"],
        "sss_mpf": sss["mpf_employer"],
        "sss_ec": sss["ec"],
        "philhealth": philhealth_employer,
        "pagibig": pagibig_employer,
    }

    employer["total"] = money(sum(employer.values(), ZERO))

    return {
        "employee_deductions": employee_deductions,
        "total_employee": money(total_employee),
        "employer": employer,
    }


def calculate_withholding_tax(
    employee,
    payroll_period,
    taxable_compensation,
    employee_statutory_deductions,
):
    taxable_income = max(
        ZERO,
        taxable_compensation - employee_statutory_deductions,
    )

    if taxable_income <= 0:
        return ZERO

    if employee.pay_frequency == "Monthly":
        tax_frequency = "Semi-monthly"
    elif employee.pay_frequency == "Weekly":
        tax_frequency = "Weekly"
    elif employee.pay_frequency == "Daily":
        tax_frequency = "Daily"
    else:
        raise ValueError("Invalid employee pay frequency.")

    tax_brackets = WithholdingTaxBracket.objects.filter(
        pay_frequency=tax_frequency,
        is_active=True,
        effective_date__lte=payroll_period.start_date,
    ).order_by("minimum_taxable_income")

    if not tax_brackets.exists():
        raise ValueError(f"No active {tax_frequency} withholding-tax brackets found.")

    if tax_frequency == "Daily":
        attendance_days = (
            Attendance.objects.filter(
                employee=employee,
                date__range=(
                    payroll_period.start_date,
                    payroll_period.end_date,
                ),
                working_hours__gt=0,
            )
            .values("date")
            .distinct()
            .count()
        )

        days = max(attendance_days, 1)
        taxable_income_per_day = taxable_income / Decimal(days)
        tax_per_day = calculate_tax_from_brackets(
            tax_brackets,
            taxable_income_per_day,
        )

        return money(tax_per_day * Decimal(days))

    return money(
        calculate_tax_from_brackets(
            tax_brackets,
            taxable_income,
        )
    )


def calculate_tax_from_brackets(tax_brackets, taxable_income):
    selected_bracket = None

    for bracket in tax_brackets:
        if bracket.minimum_taxable_income <= taxable_income:
            selected_bracket = bracket
        else:
            break

    if selected_bracket is None:
        return ZERO

    tax = (
        selected_bracket.base_tax
        + (taxable_income - selected_bracket.minimum_taxable_income)
        * selected_bracket.tax_rate
    )

    return max(ZERO, tax)


def calculate_deductions(employee, payroll_period):
    gross = calculate_gross_pay(employee, payroll_period)
    statutory = calculate_statutory_contributions(
        employee,
        payroll_period,
    )

    absence = calculate_absence_deduction(
        employee,
        payroll_period,
    )

    deduction_items = list(statutory["employee_deductions"])
    total_deductions = statutory["total_employee"]

    deduction_rules = DeductionRule.objects.filter(
        is_active=True,
        effective_date__lte=payroll_period.start_date,
    )

    for rule in deduction_rules:
        if rule.calculation_basis == "Basic Pay":
            basis_amount = gross["basic_pay"]
        else:
            basis_amount = gross["gross_pay"]

        if rule.calculation_type == "Percentage":
            amount = basis_amount * rule.employee_rate / ONE_HUNDRED
        else:
            amount = rule.employee_rate

        amount = money(amount)

        if amount > 0:
            deduction_items.append(
                {
                    "name": rule.name,
                    "amount": amount,
                }
            )
            total_deductions += amount

    deduction_items.extend(absence["deduction_items"])
    total_deductions += absence["total_deduction"]

    taxable_compensation = (
        gross["basic_pay"]
        + gross["overtime_pay"]
        + gross["taxable_allowances"]
        - absence["total_deduction"]
    )

    withholding_tax = calculate_withholding_tax(
        employee,
        payroll_period,
        taxable_compensation,
        statutory["total_employee"],
    )

    if withholding_tax > 0:
        deduction_items.append(
            {
                "name": "Withholding Tax",
                "amount": withholding_tax,
            }
        )
        total_deductions += withholding_tax

    return {
        "deduction_items": deduction_items,
        "total_deductions": money(total_deductions),
        "employer_contributions": statutory["employer"],
    }


def calculate_net_pay(employee, payroll_period):
    gross = calculate_gross_pay(employee, payroll_period)
    deductions = calculate_deductions(employee, payroll_period)

    net_pay = gross["gross_pay"] - deductions["total_deductions"]

    return {
        "gross_pay": gross["gross_pay"],
        "total_deductions": deductions["total_deductions"],
        "net_pay": money(net_pay),
    }


@transaction.atomic
def generate_payroll(payroll_period):
    if payroll_period.status == "Completed":
        raise ValueError("This payroll period is already completed.")

    if PayrollRecord.objects.filter(payroll_period=payroll_period).exists():
        raise ValueError(
            "Payroll records already exist for this period. "
            "Regeneration is not allowed."
        )

    employees = Employee.objects.filter(
        is_active=True,
        pay_frequency=payroll_period.frequency,
    )

    if not employees.exists():
        raise ValueError("No active employees found.")

    generated_records = []

    for employee in employees:
        basic = calculate_basic_pay(employee, payroll_period)
        gross = calculate_gross_pay(employee, payroll_period)
        deductions = calculate_deductions(employee, payroll_period)

        net_pay = money(gross["gross_pay"] - deductions["total_deductions"])

        record = PayrollRecord.objects.create(
            employee=employee,
            payroll_period=payroll_period,
            basic_pay=gross["basic_pay"],
            overtime_pay=gross["overtime_pay"],
            allowances=gross["allowances"],
            gross_pay=gross["gross_pay"],
            total_deductions=deductions["total_deductions"],
            net_pay=net_pay,
            total_working_hours=(basic["regular_hours"] + basic["overtime_hours"]),
            total_overtime_hours=basic["overtime_hours"],
            status="Processed",
            processed_at=timezone.now(),
        )

        PayrollItem.objects.create(
            payroll_record=record,
            description="Basic Pay",
            item_type="Earning",
            amount=gross["basic_pay"],
        )

        PayrollItem.objects.create(
            payroll_record=record,
            description="Overtime Pay",
            item_type="Earning",
            amount=gross["overtime_pay"],
        )

        if gross["taxable_allowances"] > 0:
            PayrollItem.objects.create(
                payroll_record=record,
                description="Taxable Allowances",
                item_type="Earning",
                amount=gross["taxable_allowances"],
            )

        if gross["non_taxable_allowances"] > 0:
            PayrollItem.objects.create(
                payroll_record=record,
                description="Non-taxable Allowances",
                item_type="Earning",
                amount=gross["non_taxable_allowances"],
            )

        for item in deductions["deduction_items"]:
            PayrollItem.objects.create(
                payroll_record=record,
                description=item["name"],
                item_type="Deduction",
                amount=item["amount"],
            )

        employer = deductions["employer_contributions"]

        EmployerContribution.objects.create(
            payroll_record=record,
            sss_contribution=employer["sss"],
            sss_mpf_contribution=employer["sss_mpf"],
            sss_ec_contribution=employer["sss_ec"],
            philhealth_contribution=employer["philhealth"],
            pagibig_contribution=employer["pagibig"],
            total_employer_contribution=employer["total"],
        )

        generated_records.append(record)

    payroll_period.status = "Processing"
    payroll_period.save(update_fields=["status"])

    return generated_records
