from django.shortcuts import render

from .models import Employee


def employee_list(request):
    employees = Employee.objects.all().order_by("employee_id")

    context = {
        "employees": employees,
    }

    return render(request, "employees/employee_list.html", context)
