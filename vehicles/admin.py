from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'model', 'registration_number', 'owner', 'last_service_date', 'created_at')
    list_filter = ('brand', 'fuel_type', 'year')
    search_fields = ('name', 'registration_number', 'owner__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
