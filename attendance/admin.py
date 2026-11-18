from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "date",
        "time_in",
        "time_out",
        "working_hours",
        "overtime_hours",
        "status",
    )

    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
    )

    list_filter = (
        "date",
        "status",
    )
