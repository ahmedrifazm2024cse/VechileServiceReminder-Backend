"""
Main URL Configuration for Vehicle Service Reminder System
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('vehicles.urls')),
    path('api/', include('services.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('contact.urls')),
    path('api/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
