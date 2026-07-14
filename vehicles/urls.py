from django.urls import path
from . import views

urlpatterns = [
    path('vehicles/', views.VehicleListCreateView.as_view(), name='vehicle_list_create'),
    path('vehicles/<str:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    path('admin/vehicles/', views.AdminVehiclesView.as_view(), name='admin_vehicles'),
    path('admin/vehicles/<str:pk>/', views.AdminVehiclesView.as_view(), name='admin_vehicle_delete'),
]
