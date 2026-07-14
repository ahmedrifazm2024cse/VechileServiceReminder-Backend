from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]
