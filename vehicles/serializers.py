"""
Serializers for vehicles app
"""

from rest_framework import serializers
from .models import Vehicle
from datetime import date


class VehicleSerializer(serializers.ModelSerializer):
    next_service_date = serializers.ReadOnlyField()
    days_until_service = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    reminder_status = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = (
            'id', 'owner', 'owner_name', 'name', 'brand', 'model',
            'registration_number', 'fuel_type', 'year', 'odometer_reading',
            'last_service_date', 'service_interval_months', 'service_interval_km',
            'insurance_expiry', 'pollution_certificate_expiry', 'notes',
            'image', 'image_url', 'next_service_date', 'days_until_service',
            'is_overdue', 'is_upcoming', 'reminder_status', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

    def get_image_url(self, obj):
        return obj.image if obj.image else None

    def get_owner_name(self, obj):
        return obj.owner.full_name

    def validate_registration_number(self, value):
        value = value.upper().strip()
        instance = self.instance
        qs = Vehicle.objects.filter(registration_number=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A vehicle with this registration number already exists.')
        return value

    def validate_year(self, value):
        current_year = date.today().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(f'Year must be between 1900 and {current_year + 1}.')
        return value

    def validate_odometer_reading(self, value):
        if value < 0:
            raise serializers.ValidationError('Odometer reading cannot be negative.')
        return value

    def validate_service_interval_months(self, value):
        if value < 1 or value > 120:
            raise serializers.ValidationError('Service interval must be between 1 and 120 months.')
        return value


class VehicleListSerializer(serializers.ModelSerializer):
    next_service_date = serializers.ReadOnlyField()
    days_until_service = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = (
            'id', 'name', 'brand', 'model', 'registration_number',
            'fuel_type', 'year', 'next_service_date', 'days_until_service',
            'is_overdue', 'is_upcoming', 'image_url', 'created_at'
        )

    def get_image_url(self, obj):
        return obj.image if obj.image else None
