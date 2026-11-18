from django.shortcuts import render, redirect, get_object_or_404
from .models import Attendance
from .forms import AttendanceForm
from datetime import datetime, timedelta
from decimal import Decimal


def attendance_list(request):
    attendance_records = Attendance.objects.select_related("employee").all()

    context = {
        "attendance_records": attendance_records,
    }

    return render(request, "attendance/attendance_list.html", context)


def attendance_create(request):
    if request.method == "POST":
        form = AttendanceForm(request.POST)

        if form.is_valid():
            attendance = form.save(commit=False)

            if attendance.time_in and attendance.time_out:
                start = datetime.combine(attendance.date, attendance.time_in)

                end = datetime.combine(attendance.date, attendance.time_out)

                if end < start:
                    end += timedelta(days=1)

                total_hours = (end - start).total_seconds() / 3600

                attendance.working_hours = Decimal(str(total_hours)).quantize(
                    Decimal("0.01")
                )

            else:
                attendance.working_hours = Decimal("0.00")

            attendance.save()
            return redirect("attendance_list")

    else:
        form = AttendanceForm()

    context = {
        "form": form,
    }

    return render(request, "attendance/attendance_form.html", context)


def attendance_update(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == "POST":
        form = AttendanceForm(request.POST, instance=attendance)

        if form.is_valid():
            attendance = form.save(commit=False)

            if attendance.time_in and attendance.time_out:
                start = datetime.combine(attendance.date, attendance.time_in)

                end = datetime.combine(attendance.date, attendance.time_out)

                if end < start:
                    end += timedelta(days=1)

                total_hours = (end - start).total_seconds() / 3600

                attendance.working_hours = Decimal(str(total_hours)).quantize(
                    Decimal("0.01")
                )

            else:
                attendance.working_hours = Decimal("0.00")

            attendance.save()
            return redirect("attendance_list")

    else:
        form = AttendanceForm(instance=attendance)

    return render(request, "attendance/attendance_form.html", {"form": form})


def attendance_delete(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == "POST":
        attendance.delete()

    return redirect("attendance_list")
