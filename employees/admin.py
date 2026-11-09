from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "position",
        "department",
        "employment_type",
        "basic_salary",
        "is_active",
    )

    search_fields = (
        "employee_id",
        "first_name",
        "last_name",
        "department",
    )

    list_filter = (
        "department",
        "employment_type",
        "is_active",
    )
