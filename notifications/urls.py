from django.urls import path
from . import views

urlpatterns = [
    path('reminders/', views.ReminderView.as_view(), name='reminders'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/', views.NotificationMarkReadView.as_view(), name='mark_all_read'),
    path('notifications/<str:pk>/read/', views.NotificationMarkReadView.as_view(), name='mark_read'),
    path('admin/reminder-logs/', views.AdminReminderLogsView.as_view(), name='admin_reminder_logs'),
    path('admin/trigger-reminders/', views.TriggerReminderView.as_view(), name='trigger_reminders'),
]
