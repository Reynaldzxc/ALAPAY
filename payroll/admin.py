from django.contrib import admin
from .models import (
    PayrollPeriod, 
    DeductionRule, 
    OvertimeRule, 
    PayrollRecord, 
    PayrollItem, 
    PayrollSettings,
    SSSContributionBracket,
    StatutoryContributionRule,
    WithholdingTaxBracket,
    EmployerContribution,
)
from django.urls import reverse
from django.utils.html import format_html


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_date",
        "end_date",
        "pay_date",
        "status",
    )

    list_filter = ("status", "start_date")
    search_fields = ("name",)
    ordering = ("-start_date",)
    readonly_fields = ("created_at",)

@admin.register(DeductionRule)
class DeductionRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "calculation_type",
        "calculation_basis",
        "employee_rate",
        "employer_rate",
        "effective_date",
        "is_active",
    )

    list_filter = ("calculation_type", "is_active")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at",)


@admin.register(OvertimeRule)
class OvertimeRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "multiplier",
        "effective_date",
        "is_active",
    )

    list_filter = ("is_active", "effective_date")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at",)

@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "payroll_period",
        "basic_pay",
        "overtime_pay",
        "gross_pay",
        "total_deductions",
        "net_pay",
        "status",
        "payslip_link",
    )

    list_filter = ("status", "payroll_period")
    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "processed_at")

    @admin.display(description="Payslip")
    def payslip_link(self, obj):
        url = reverse("payroll:payslip-detail", args=[obj.pk])
        return format_html('<a href="{}">View Payslip</a>', url)


@admin.register(PayrollItem)
class PayrollItemAdmin(admin.ModelAdmin):
    list_display = (
        "payroll_record",
        "description",
        "item_type",
        "amount",
        "created_at",
    )

    list_filter = ("item_type", "created_at")
    search_fields = (
        "description",
        "payroll_record__employee__employee_id",
        "payroll_record__employee__first_name",
        "payroll_record__employee__last_name",
    )

    readonly_fields = ("created_at",)


@admin.register(PayrollSettings)
class PayrollSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "standard_hours_per_day",
        "weekly_working_days",
        "monthly_working_days",
        "effective_date",
        "is_active",
    )

    list_filter = (
        "is_active",
        "effective_date",
    )

    ordering = ("-effective_date",)

    readonly_fields = ("created_at",)


@admin.register(SSSContributionBracket)
class SSSContributionBracketAdmin(admin.ModelAdmin):
    list_display = (
        "minimum_compensation",
        "maximum_compensation",
        "monthly_salary_credit",
        "employee_contribution",
        "employee_mpf_contribution",
        "employer_contribution",
        "employer_mpf_contribution",
        "employer_ec_contribution",
        "effective_date",
        "is_active",
    )
    list_filter = ("is_active", "effective_date")
    ordering = ("minimum_compensation",)


@admin.register(StatutoryContributionRule)
class StatutoryContributionRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "employee_rate",
        "employer_rate",
        "minimum_monthly_salary",
        "maximum_monthly_salary",
        "effective_date",
        "is_active",
    )
    list_filter = ("name", "is_active", "effective_date")
    ordering = ("name", "-effective_date")


@admin.register(WithholdingTaxBracket)
class WithholdingTaxBracketAdmin(admin.ModelAdmin):
    list_display = (
        "pay_frequency",
        "minimum_taxable_income",
        "maximum_taxable_income",
        "base_tax",
        "tax_rate",
        "effective_date",
        "is_active",
    )
    list_filter = ("pay_frequency", "is_active", "effective_date")
    ordering = ("pay_frequency", "minimum_taxable_income")


@admin.register(EmployerContribution)
class EmployerContributionAdmin(admin.ModelAdmin):
    list_display = (
        "payroll_record",
        "sss_contribution",
        "sss_mpf_contribution",
        "sss_ec_contribution",
        "philhealth_contribution",
        "pagibig_contribution",
        "total_employer_contribution",
    )
    search_fields = (
        "payroll_record__employee__employee_id",
        "payroll_record__employee__first_name",
        "payroll_record__employee__last_name",
    )