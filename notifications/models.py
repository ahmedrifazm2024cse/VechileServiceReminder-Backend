"""
Notification and Reminder models
"""

import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from vehicles.models import Vehicle
from accounts.models import User


class Reminder(models.Model):
    REMINDER_DAY_CHOICES = [
        (1, '1 Day Before'),
        (3, '3 Days Before'),
        (7, '7 Days Before'),
        (15, '15 Days Before'),
        (30, '30 Days Before'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, related_name='reminder')
    is_enabled = models.BooleanField(default=False)
    reminder_days = models.JSONField(default=list)  # e.g. [30, 15, 7, 3, 1]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reminders'

    def __str__(self):
        return f"Reminder for {self.vehicle.name} - {'Enabled' if self.is_enabled else 'Disabled'}"


class ReminderLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reminder_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminder_logs')
    email_sent_to = models.EmailField()
    reminder_days = models.IntegerField()  # Which day trigger: 30, 15, 7, 3, 1
    service_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'reminder_logs'
        ordering = ['-sent_at']

    def __str__(self):
        return f"Reminder Log - {self.vehicle.name} - {self.status} - {self.sent_at}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('reminder', 'Service Reminder'),
        ('overdue', 'Service Overdue'),
        ('insurance', 'Insurance Expiry'),
        ('puc', 'Pollution Certificate Expiry'),
        ('system', 'System Notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    related_vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"
