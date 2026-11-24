from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("employees/", include("employees.urls")),
    path("attendance/", include("attendance.urls")),
    path("benefits/", include("benefits.urls")),
    path("payroll/", include("payroll.urls")),
    path("", include("employees.urls")),
]
