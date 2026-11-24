from django.shortcuts import render, redirect
from .models import Employee
from .forms import EmployeeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.db.models import Sum, Count
from payroll.models import PayrollRecord


@login_required
@permission_required("employees.view_employee", raise_exception=True)
def employee_list(request):
    employees = Employee.objects.all().order_by("employee_id")

    search_query = request.GET.get("search", "")
    department_filter = request.GET.get("department", "")
    employment_filter = request.GET.get("employment_type", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        employees = employees.filter(
            models.Q(employee_id__icontains=search_query)
            | models.Q(first_name__icontains=search_query)
            | models.Q(last_name__icontains=search_query)
        )

    if department_filter:
        employees = employees.filter(department=department_filter)

    if employment_filter:
        employees = employees.filter(employment_type=employment_filter)

    if status_filter == "active":
        employees = employees.filter(is_active=True)
    elif status_filter == "inactive":
        employees = employees.filter(is_active=False)

    departments = (
        Employee.objects.values_list("department", flat=True)
        .distinct()
        .order_by("department")
    )

    context = {
        "employees": employees,
        "search_query": search_query,
        "departments": departments,
        "department_filter": department_filter,
        "employment_filter": employment_filter,
        "status_filter": status_filter,
    }

    return render(request, "employees/employee_list.html", context)


@login_required
@permission_required("employees.add_employee", raise_exception=True)
def employee_create(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("employee_list")

    else:
        form = EmployeeForm()

    context = {
        "form": form,
    }

    return render(request, "employees/employee_form.html", context)


@login_required
@permission_required("employees.change_employee", raise_exception=True)
def employee_update(request, pk):
    employee = Employee.objects.get(pk=pk)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)

        if form.is_valid():
            form.save()
            return redirect("employee_list")

    else:
        form = EmployeeForm(instance=employee)

    context = {
        "form": form,
        "employee": employee,
    }

    return render(request, "employees/employee_form.html", context)


@login_required
@permission_required("employees.change_employee", raise_exception=True)
def employee_deactivate(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        employee.is_active = False
        employee.save()
        return redirect("employee_list")

    return redirect("employee_list")


@login_required
def dashboard_redirect(request):
    user = request.user

    is_admin = user.is_superuser or user.groups.filter(name="Administrator").exists()

    is_hr = user.groups.filter(name="HR Staff").exists()
    is_payroll = user.groups.filter(name="Payroll Staff").exists()

    if not (is_admin or is_hr or is_payroll):
        return redirect("login")

    employee_count = Employee.objects.count()
    active_employees = Employee.objects.filter(is_active=True).count()
    inactive_employees = Employee.objects.filter(is_active=False).count()

    payroll_records = PayrollRecord.objects.all()

    if is_hr and not is_admin and not is_payroll:
        payroll_records = PayrollRecord.objects.none()

    payroll_summary = payroll_records.aggregate(
        total_records=Count("id"),
        total_gross=Sum("gross_pay"),
        total_net=Sum("net_pay"),
    )

    paid_count = payroll_records.filter(status="Paid").count()

    pending_count = payroll_records.exclude(status="Paid").count()

    recent_payrolls = payroll_records.select_related(
        "employee", "payroll_period"
    ).order_by("-created_at")[:5]

    context = {
        "employee_count": employee_count,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_records": payroll_summary["total_records"] or 0,
        "total_gross": payroll_summary["total_gross"] or 0,
        "total_net": payroll_summary["total_net"] or 0,
        "paid_count": paid_count,
        "pending_count": pending_count,
        "recent_payrolls": recent_payrolls,
        "is_admin": is_admin,
        "is_hr": is_hr,
        "is_payroll": is_payroll,
    }

    return render(request, "employees/dashboard.html", context)
