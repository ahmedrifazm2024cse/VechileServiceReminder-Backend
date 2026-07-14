"""
Views for notifications app
"""

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from vehicles.models import Vehicle
from .models import Reminder, ReminderLog, Notification
from .serializers import ReminderSerializer, ReminderLogSerializer, NotificationSerializer


class ReminderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vehicle_id = request.query_params.get('vehicle_id', '')
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, owner=request.user)
                reminder, _ = Reminder.objects.get_or_create(
                    vehicle=vehicle,
                    defaults={'is_enabled': False, 'reminder_days': [30, 15, 7, 1]}
                )
                return Response({
                    'success': True,
                    'reminder': ReminderSerializer(reminder).data
                })
            except Vehicle.DoesNotExist:
                return Response({'detail': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get all reminders for user's vehicles
        reminders = Reminder.objects.filter(vehicle__owner=request.user)
        return Response({
            'success': True,
            'reminders': ReminderSerializer(reminders, many=True).data
        })

    def put(self, request):
        vehicle_id = request.data.get('vehicle_id')
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, owner=request.user)
        except Vehicle.DoesNotExist:
            return Response({'detail': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)

        reminder, _ = Reminder.objects.get_or_create(
            vehicle=vehicle,
            defaults={'is_enabled': False, 'reminder_days': [30, 15, 7, 1]}
        )

        serializer = ReminderSerializer(reminder, data=request.data, partial=True)
        if serializer.is_valid():
            reminder = serializer.save()
            return Response({
                'success': True,
                'message': f"Reminder {'enabled' if reminder.is_enabled else 'disabled'} successfully.",
                'reminder': ReminderSerializer(reminder).data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        unread_count = sum(1 for n in notifications if not n.is_read)
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'success': True,
            'count': notifications.count(),
            'unread_count': unread_count,
            'notifications': serializer.data
        })


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk=None):
        if pk:
            # Mark single notification as read
            try:
                notification = Notification.objects.get(pk=pk, user=request.user)
                notification.is_read = True
                notification.save()
                return Response({'success': True, 'message': 'Notification marked as read.'})
            except Notification.DoesNotExist:
                return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Mark all as read
            for n in Notification.objects.filter(user=request.user):
                if not n.is_read:
                    n.is_read = True
                    n.save()
            return Response({'success': True, 'message': 'All notifications marked as read.'})


class AdminReminderLogsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        logs = ReminderLog.objects.all().select_related('vehicle', 'user')
        status_filter = request.query_params.get('status', '')
        if status_filter:
            logs = logs.filter(status=status_filter)

        serializer = ReminderLogSerializer(logs, many=True)
        return Response({
            'success': True,
            'count': logs.count(),
            'logs': serializer.data
        })


class TriggerReminderView(APIView):
    """Manually trigger reminders (Admin only)"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        from .scheduler import send_service_reminders
        try:
            send_service_reminders()
            return Response({'success': True, 'message': 'Reminders triggered successfully.'})
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to trigger reminders: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
