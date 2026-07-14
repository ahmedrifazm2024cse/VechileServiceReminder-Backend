from django.contrib import admin
from .models import Reminder, ReminderLog, Notification


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'is_enabled', 'reminder_days', 'updated_at')
    list_filter = ('is_enabled',)
    search_fields = ('vehicle__name', 'vehicle__registration_number')


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'user', 'email_sent_to', 'reminder_days', 'service_due_date', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('vehicle__name', 'user__email')
    readonly_fields = ('sent_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'user__email')
