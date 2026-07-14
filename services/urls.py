from django.urls import path
from . import views

urlpatterns = [
    path('services/', views.ServiceHistoryListCreateView.as_view(), name='service_list_create'),
    path('services/<str:pk>/', views.ServiceHistoryDetailView.as_view(), name='service_detail'),
    path('services/export/', views.ExportServicesView.as_view(), name='export_services'),
    path('admin/services/', views.AdminServicesView.as_view(), name='admin_services'),
]
