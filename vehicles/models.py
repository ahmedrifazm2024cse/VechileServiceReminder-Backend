"""
Vehicle models for Vehicle Service Reminder System
"""

import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import User


FUEL_TYPE_CHOICES = [
    ('petrol', 'Petrol'),
    ('diesel', 'Diesel'),
    ('electric', 'Electric'),
    ('hybrid', 'Hybrid'),
    ('cng', 'CNG'),
    ('lpg', 'LPG'),
    ('other', 'Other'),
]


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, unique=True)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES, default='petrol')
    year = models.IntegerField()
    odometer_reading = models.FloatField(default=0)
    last_service_date = models.DateField()
    service_interval_months = models.IntegerField(default=6)
    service_interval_km = models.FloatField(default=5000)
    insurance_expiry = models.DateField(null=True, blank=True)
    pollution_certificate_expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    image = models.URLField(max_length=1024, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.registration_number}"

    @property
    def next_service_date(self):
        from dateutil.relativedelta import relativedelta
        try:
            from dateutil.relativedelta import relativedelta
            return self.last_service_date + relativedelta(months=self.service_interval_months)
        except ImportError:
            # fallback without dateutil
            month = self.last_service_date.month - 1 + self.service_interval_months
            year = self.last_service_date.year + month // 12
            month = month % 12 + 1
            import calendar
            day = min(self.last_service_date.day, calendar.monthrange(year, month)[1])
            from datetime import date
            return date(year, month, day)

    @property
    def days_until_service(self):
        from datetime import date
        delta = self.next_service_date - date.today()
        return delta.days

    @property
    def is_overdue(self):
        return self.days_until_service < 0

    @property
    def is_upcoming(self):
        return 0 <= self.days_until_service <= 30

    @property
    def reminder_status(self):
        try:
            reminder = self.reminder
            return reminder.is_enabled
        except Exception:
            return False
