from django.contrib import admin
from .models import Allowance, LeaveRequest, LeaveBalance


@admin.register(Allowance)
class AllowanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "name",
        "benefit_type",
        "amount",
        "frequency",
        "start_date",
        "end_date",
        "is_taxable",
        "is_active",
    )

    list_filter = (
        "benefit_type",
        "frequency",
        "is_taxable",
        "is_active",
    )

    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
        "name",
    )

    ordering = ("employee", "name")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "leave_type",
        "start_date",
        "end_date",
        "status",
        "is_paid",
        "created_at",
    )

    list_filter = (
        "leave_type",
        "status",
        "is_paid",
        "start_date",
    )

    list_editable = ("is_paid",)

    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
    )

    ordering = ("-created_at",)


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "leave_type",
        "year",
        "allocated_days",
        "used_days",
        "remaining_days",
    )

    list_filter = (
        "leave_type",
        "year",
    )

    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
    )

    ordering = ("employee", "leave_type", "year")   