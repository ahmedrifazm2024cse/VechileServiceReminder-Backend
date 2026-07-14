"""
Serializers for notifications app
"""

from rest_framework import serializers
from .models import Reminder, ReminderLog, Notification


class ReminderSerializer(serializers.ModelSerializer):
    vehicle_name = serializers.SerializerMethodField()
    vehicle_registration = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = (
            'id', 'vehicle', 'vehicle_name', 'vehicle_registration',
            'is_enabled', 'reminder_days', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'vehicle', 'created_at', 'updated_at')

    def get_vehicle_name(self, obj):
        return obj.vehicle.name

    def get_vehicle_registration(self, obj):
        return obj.vehicle.registration_number

    def validate_reminder_days(self, value):
        allowed = [1, 3, 7, 15, 30]
        for day in value:
            if day not in allowed:
                raise serializers.ValidationError(
                    f'Invalid reminder day: {day}. Allowed values are {allowed}.'
                )
        return list(set(value))  # Remove duplicates


class ReminderLogSerializer(serializers.ModelSerializer):
    vehicle_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = ReminderLog
        fields = (
            'id', 'vehicle', 'vehicle_name', 'user', 'user_email',
            'email_sent_to', 'reminder_days', 'service_due_date',
            'status', 'sent_at', 'error_message'
        )
        read_only_fields = ('id', 'sent_at')

    def get_vehicle_name(self, obj):
        return obj.vehicle.name

    def get_user_email(self, obj):
        return obj.user.email


class NotificationSerializer(serializers.ModelSerializer):
    related_vehicle_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            'id', 'title', 'message', 'notification_type',
            'is_read', 'related_vehicle', 'related_vehicle_name', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def get_related_vehicle_name(self, obj):
        if obj.related_vehicle:
            return obj.related_vehicle.name
        return None
