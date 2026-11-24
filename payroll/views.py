from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from django.db import models
from django.db.models import Sum, Count
from django.http import HttpResponse

from .models import PayrollRecord, PayrollPeriod
from .services import generate_payroll
from .forms import PayrollPeriodForm
from employees.models import Employee
from django.contrib.auth.decorators import login_required, permission_required

import csv


@login_required
@permission_required("payroll.view_payrollrecord", raise_exception=True)
def payslip_detail(request, pk):
    payroll_record = get_object_or_404(
        PayrollRecord.objects.select_related(
            "employee",
            "payroll_period",
        ).prefetch_related("items"),
        pk=pk,
    )

    context = {
        "payroll_record": payroll_record,
        "items": payroll_record.items.all(),
    }

    return render(request, "payroll/payslip_detail.html", context)


@login_required
@permission_required("payroll.add_payrollrecord", raise_exception=True)
def payroll_generate(request):
    periods = PayrollPeriod.objects.all()

    if request.method == "POST":
        period_id = request.POST.get("payroll_period")
        period = get_object_or_404(PayrollPeriod, pk=period_id)

        try:
            records = generate_payroll(period)
            messages.success(
                request,
                f"Successfully generated {len(records)} payroll record(s).",
            )
        except ValueError as error:
            messages.error(request, str(error))

        return redirect("payroll:payroll-generate")

    return render(
        request,
        "payroll/payroll_generate.html",
        {"periods": periods},
    )


@login_required
@permission_required("payroll.view_payrollperiod", raise_exception=True)
def payroll_period_list(request):
    periods = PayrollPeriod.objects.all()

    return render(
        request,
        "payroll/payroll_period_list.html",
        {"periods": periods},
    )


@login_required
@permission_required("payroll.add_payrollperiod", raise_exception=True)
def payroll_period_create(request):
    if request.method == "POST":
        form = PayrollPeriodForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Payroll period created successfully.",
            )
            return redirect("payroll:payroll-period-list")
    else:
        form = PayrollPeriodForm()

    return render(
        request,
        "payroll/payroll_period_form.html",
        {"form": form},
    )


@login_required
@permission_required("payroll.change_payrollperiod", raise_exception=True)
def payroll_period_update(request, pk):
    period = get_object_or_404(PayrollPeriod, pk=pk)

    if period.payroll_records.exists():
        messages.error(
            request,
            "This payroll period cannot be edited because payroll records have already been generated.",
        )
        return redirect("payroll:payroll-period-list")

    if request.method == "POST":
        form = PayrollPeriodForm(request.POST, instance=period)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Payroll period updated successfully.",
            )
            return redirect("payroll:payroll-period-list")
    else:
        form = PayrollPeriodForm(instance=period)

    return render(
        request,
        "payroll/payroll_period_form.html",
        {
            "form": form,
            "page_title": "Edit Payroll Period",
        },
    )


@login_required
@permission_required("payroll.view_payrollrecord", raise_exception=True)
def payroll_record_list(request):
    records = PayrollRecord.objects.select_related(
        "employee",
        "payroll_period",
    ).all()

    search_query = request.GET.get("search", "")
    period_id = request.GET.get("period", "")
    status = request.GET.get("status", "")
    department = request.GET.get("department", "")

    if search_query:
        records = records.filter(
            models.Q(employee__employee_id__icontains=search_query)
            | models.Q(employee__first_name__icontains=search_query)
            | models.Q(employee__last_name__icontains=search_query)
        )

    if period_id:
        records = records.filter(payroll_period_id=period_id)

    if status:
        records = records.filter(status=status)

    if department:
        records = records.filter(employee__department=department)

    periods = PayrollPeriod.objects.all()

    departments = (
        Employee.objects.order_by("department")
        .values_list("department", flat=True)
        .distinct()
    )

    return render(
        request,
        "payroll/payroll_record_list.html",
        {
            "records": records,
            "periods": periods,
            "departments": departments,
            "search_query": search_query,
            "selected_period": period_id,
            "selected_status": status,
            "selected_department": department,
        },
    )


@login_required
@permission_required("payroll.view_payrollrecord", raise_exception=True)
def payroll_summary(request):
    periods = PayrollPeriod.objects.all()
    employees = Employee.objects.all().order_by("employee_id")

    period_id = request.GET.get("period", "")
    employee_id = request.GET.get("employee", "")

    records = PayrollRecord.objects.select_related(
        "employee",
        "payroll_period",
    )

    if period_id:
        records = records.filter(payroll_period_id=period_id)

    if employee_id:
        records = records.filter(employee_id=employee_id)

    summary = records.aggregate(
        employee_count=Count("id"),
        paid_count=Count("id", filter=models.Q(status="Paid")),
        pending_count=Count("id", filter=~models.Q(status="Paid")),
        total_basic_pay=Sum("basic_pay"),
        total_overtime_pay=Sum("overtime_pay"),
        total_allowances=Sum("allowances"),
        total_gross_pay=Sum("gross_pay"),
        total_deductions=Sum("total_deductions"),
        total_net_pay=Sum("net_pay"),
    )

    return render(
        request,
        "payroll/payroll_summary.html",
        {
            "periods": periods,
            "employees": employees,
            "selected_period": period_id,
            "selected_employee": employee_id,
            "summary": summary,
        },
    )


@login_required
@permission_required("payroll.view_payrollrecord", raise_exception=True)
def payroll_summary_export(request):
    period_id = request.GET.get("period", "")
    employee_id = request.GET.get("employee", "")

    records = PayrollRecord.objects.select_related(
        "employee",
        "payroll_period",
    ).all()

    if period_id:
        records = records.filter(payroll_period_id=period_id)

    if employee_id:
        records = records.filter(employee_id=employee_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="alapay_payroll_summary.csv"'
    )

    writer = csv.writer(response)

    writer.writerow(
        [
            "Employee ID",
            "Employee Name",
            "Department",
            "Payroll Period",
            "Basic Pay",
            "Overtime Pay",
            "Allowances",
            "Gross Pay",
            "Total Deductions",
            "Net Pay",
            "Status",
        ]
    )

    for record in records:
        writer.writerow(
            [
                record.employee.employee_id,
                f"{record.employee.first_name} {record.employee.last_name}",
                record.employee.department,
                record.payroll_period.name,
                record.basic_pay,
                record.overtime_pay,
                record.allowances,
                record.gross_pay,
                record.total_deductions,
                record.net_pay,
                record.status,
            ]
        )

    return response


@login_required
@permission_required("payroll.change_payrollrecord", raise_exception=True)
def payroll_record_update_status(request, pk):

    record = get_object_or_404(
        PayrollRecord.objects.select_related("payroll_period"),
        pk=pk,
    )

    if request.method == "POST":
        new_status = request.POST.get("status")

        allowed_transitions = {
            "Processed": ["Approved"],
            "Approved": ["Paid"],
        }

        if new_status in allowed_transitions.get(record.status, []):
            record.status = new_status
            record.save(update_fields=["status"])

            if new_status == "Paid":
                payroll_period = record.payroll_period

                if not payroll_period.payroll_records.exclude(status="Paid").exists():
                    payroll_period.status = "Completed"
                    payroll_period.save(update_fields=["status"])

            messages.success(
                request,
                f"Payroll record successfully updated to {new_status}.",
            )
        else:
            messages.error(
                request,
                "Invalid payroll status transition.",
            )

    return redirect("payroll:payroll-record-list")
