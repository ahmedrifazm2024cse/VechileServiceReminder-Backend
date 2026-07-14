"""
Serializers for services app
"""

from rest_framework import serializers
from .models import ServiceHistory


class ServiceHistorySerializer(serializers.ModelSerializer):
    vehicle_name = serializers.SerializerMethodField()
    vehicle_registration = serializers.SerializerMethodField()
    invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = ServiceHistory
        fields = (
            'id', 'vehicle', 'vehicle_name', 'vehicle_registration',
            'service_date', 'odometer', 'cost', 'service_center',
            'description', 'invoice', 'invoice_url', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_vehicle_name(self, obj):
        return obj.vehicle.name

    def get_vehicle_registration(self, obj):
        return obj.vehicle.registration_number

    def get_invoice_url(self, obj):
        request = self.context.get('request')
        if obj.invoice and request:
            return request.build_absolute_uri(obj.invoice.url)
        return None

    def validate_odometer(self, value):
        if value < 0:
            raise serializers.ValidationError('Odometer reading cannot be negative.')
        return value

    def validate_cost(self, value):
        if value < 0:
            raise serializers.ValidationError('Cost cannot be negative.')
        return value
