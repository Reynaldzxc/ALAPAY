from django.urls import path
from . import views

app_name = "benefits"

urlpatterns = [
    # Leave Management
    path(
        "leave/",
        views.leave_request_list,
        name="leave-request-list",
    ),
    path(
        "leave/create/",
        views.leave_request_create,
        name="leave-request-create",
    ),
    path(
        "leave/<int:pk>/approve/",
        views.leave_request_approve,
        name="leave-request-approve",
    ),
    path(
        "leave/<int:pk>/reject/",
        views.leave_request_reject,
        name="leave-request-reject",
    ),
    path(
        "leave/balances/",
        views.leave_balance_list,
        name="leave-balance-list",
    ),
    # Allowance Management
    path(
        "allowances/",
        views.allowance_list,
        name="allowance-list",
    ),
    path(
        "allowances/create/",
        views.allowance_create,
        name="allowance-create",
    ),
    path(
        "allowances/<int:pk>/edit/",
        views.allowance_update,
        name="allowance-update",
    ),
    path(
        "allowances/<int:pk>/delete/",
        views.allowance_delete,
        name="allowance-delete",
    ),
]
