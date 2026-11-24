from django.shortcuts import render, redirect, get_object_or_404
from .models import Attendance
from .forms import AttendanceForm
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required


def calculate_working_hours(attendance):
    if not attendance.time_in or not attendance.time_out:
        attendance.overtime_hours = Decimal("0.00")
        return Decimal("0.00")

    start = datetime.combine(attendance.date, attendance.time_in)
    end = datetime.combine(attendance.date, attendance.time_out)

    if end < start:
        end += timedelta(days=1)

    total_hours = Decimal(str((end - start).total_seconds() / 3600))

    lunch_break = Decimal("1.00")

    working_hours = max(total_hours - lunch_break, Decimal("0.00"))

    standard_hours = Decimal("8.00")

    overtime = max(working_hours - standard_hours, Decimal("0.00"))

    attendance.overtime_hours = overtime.quantize(Decimal("0.01"))

    return working_hours.quantize(Decimal("0.01"))


@login_required
@permission_required("attendance.view_attendance", raise_exception=True)
def attendance_list(request):
    attendance_records = Attendance.objects.select_related("employee").all()

    context = {
        "attendance_records": attendance_records,
    }

    return render(request, "attendance/attendance_list.html", context)


@login_required
@permission_required("attendance.view_attendance", raise_exception=True)
def attendance_create(request):
    if request.method == "POST":
        form = AttendanceForm(request.POST)

        if form.is_valid():
            attendance = form.save(commit=False)

            attendance.working_hours = calculate_working_hours(attendance)

            attendance.save()
            return redirect("attendance_list")

    else:
        form = AttendanceForm()

    context = {
        "form": form,
    }

    return render(request, "attendance/attendance_form.html", context)


@login_required
@permission_required("attendance.view_attendance", raise_exception=True)
def attendance_update(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == "POST":
        form = AttendanceForm(request.POST, instance=attendance)

        if form.is_valid():
            attendance = form.save(commit=False)

            attendance.working_hours = calculate_working_hours(attendance)

            attendance.save()
            return redirect("attendance_list")

    else:
        form = AttendanceForm(instance=attendance)

    return render(request, "attendance/attendance_form.html", {"form": form})


@login_required
@permission_required("attendance.view_attendance", raise_exception=True)
def attendance_delete(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == "POST":
        attendance.delete()

    return redirect("attendance_list")
