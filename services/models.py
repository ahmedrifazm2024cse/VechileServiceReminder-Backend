"""
Service History models
"""

import uuid
from django.db import models
from vehicles.models import Vehicle


class ServiceHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_history')
    service_date = models.DateField()
    odometer = models.FloatField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_center = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    invoice = models.FileField(upload_to='invoices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_history'
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.vehicle.name} - Service on {self.service_date}"
