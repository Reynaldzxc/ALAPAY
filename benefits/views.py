from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from .models import LeaveRequest, LeaveBalance, Allowance
from .forms import LeaveRequestForm, AllowanceForm

# LEAVE MANAGEMENT


@login_required
@permission_required("benefits.view_leaverequest", raise_exception=True)
def leave_request_list(request):
    leave_requests = LeaveRequest.objects.select_related("employee").all()

    return render(
        request,
        "benefits/leave_request_list.html",
        {"leave_requests": leave_requests},
    )


@login_required
@permission_required("benefits.add_leaverequest", raise_exception=True)
def leave_request_create(request):
    if request.method == "POST":
        form = LeaveRequestForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect("benefits:leave-request-list")

    else:
        form = LeaveRequestForm()

    return render(
        request,
        "benefits/leave_request_form.html",
        {"form": form},
    )


@login_required
@permission_required("benefits.change_leaverequest", raise_exception=True)
def leave_request_approve(request, pk):
    leave_request = get_object_or_404(LeaveRequest, pk=pk)

    if request.method == "POST" and leave_request.status == "Pending":
        leave_request.status = "Approved"
        leave_request.save()
        messages.success(request, "Leave request approved.")

    return redirect("benefits:leave-request-list")


@login_required
@permission_required("benefits.change_leaverequest", raise_exception=True)
def leave_request_reject(request, pk):
    leave_request = get_object_or_404(LeaveRequest, pk=pk)

    if request.method == "POST" and leave_request.status == "Pending":
        leave_request.status = "Rejected"
        leave_request.save()
        messages.success(request, "Leave request rejected.")

    return redirect("benefits:leave-request-list")


@login_required
@permission_required("benefits.view_leavebalance", raise_exception=True)
def leave_balance_list(request):
    leave_balances = LeaveBalance.objects.select_related("employee").all()

    return render(
        request,
        "benefits/leave_balance_list.html",
        {"leave_balances": leave_balances},
    )


# ALLOWANCE MANAGEMENT


@login_required
@permission_required("benefits.view_allowance", raise_exception=True)
def allowance_list(request):
    allowances = Allowance.objects.select_related("employee").all()

    return render(
        request,
        "benefits/allowance_list.html",
        {"allowances": allowances},
    )


@login_required
@permission_required("benefits.add_allowance", raise_exception=True)
def allowance_create(request):
    if request.method == "POST":
        form = AllowanceForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Allowance created successfully.")
            return redirect("benefits:allowance-list")

    else:
        form = AllowanceForm()

    return render(
        request,
        "benefits/allowance_form.html",
        {"form": form},
    )


@login_required
@permission_required("benefits.change_allowance", raise_exception=True)
def allowance_update(request, pk):
    allowance = get_object_or_404(Allowance, pk=pk)

    if request.method == "POST":
        form = AllowanceForm(request.POST, instance=allowance)

        if form.is_valid():
            form.save()
            messages.success(request, "Allowance updated successfully.")
            return redirect("benefits:allowance-list")

    else:
        form = AllowanceForm(instance=allowance)

    return render(
        request,
        "benefits/allowance_form.html",
        {
            "form": form,
            "allowance": allowance,
        },
    )


@login_required
@permission_required("benefits.delete_allowance", raise_exception=True)
def allowance_delete(request, pk):
    allowance = get_object_or_404(Allowance, pk=pk)

    if request.method == "POST":
        allowance.delete()
        messages.success(request, "Allowance deleted successfully.")

    return redirect("benefits:allowance-list")
