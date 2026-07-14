from django.urls import path
from . import views

urlpatterns = [
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('admin/contact/', views.AdminContactView.as_view(), name='admin_contact'),
    path('admin/contact/<str:pk>/', views.AdminContactView.as_view(), name='admin_contact_detail'),
]
