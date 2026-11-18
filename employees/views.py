from django.shortcuts import render, redirect
from .models import Employee
from .forms import EmployeeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models


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


def employee_deactivate(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        employee.is_active = False
        employee.save()
        return redirect("employee_list")

    return redirect("employee_list")
