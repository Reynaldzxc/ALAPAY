from django.urls import path
from . import views

urlpatterns = [
    path("", views.employee_list, name="employee_list"),
    path("add/", views.employee_create, name="employee_create"),
    path("edit/<int:pk>/", views.employee_update, name="employee_update"),
    path("deactivate/<int:pk>/", views.employee_deactivate, name="employee_deactivate"),
]
