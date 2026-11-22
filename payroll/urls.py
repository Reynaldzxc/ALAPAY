from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [
    path(
        "payslip/<int:pk>/",
        views.payslip_detail,
        name="payslip-detail",
    ),
    path(
        "generate/",
        views.payroll_generate,
        name="payroll-generate",
    ),
    path(
        "periods/",
        views.payroll_period_list,
        name="payroll-period-list",
    ),
    path(
        "periods/create/",
        views.payroll_period_create,
        name="payroll-period-create",
    ),
    path(
        "periods/<int:pk>/edit/",
        views.payroll_period_update,
        name="payroll-period-update",
    ),
    path(
        "records/",
        views.payroll_record_list,
        name="payroll-record-list",
    ),

    path(
        "summary/",
        views.payroll_summary,
        name="payroll-summary",
    ),

    path(
        "summary/export/",
        views.payroll_summary_export,
        name="payroll-summary-export",
    ),
    path(
        "records/<int:pk>/update-status/",
        views.payroll_record_update_status,
        name="payroll-record-update-status",
    ),
]