from django.contrib import admin
from .models import ServiceHistory


@admin.register(ServiceHistory)
class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_date', 'odometer', 'cost', 'service_center', 'created_at')
    list_filter = ('service_date',)
    search_fields = ('vehicle__name', 'vehicle__registration_number', 'service_center')
    ordering = ('-service_date',)
