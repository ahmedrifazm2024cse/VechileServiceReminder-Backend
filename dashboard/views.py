"""
Dashboard views - Customer and Admin statistics
"""

from datetime import date, timedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from vehicles.models import Vehicle
from services.models import ServiceHistory
from notifications.models import Reminder, ReminderLog, Notification
from accounts.models import User
from contact.models import ContactMessage


class CustomerDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        vehicles = Vehicle.objects.filter(owner=user)

        upcoming_services = []
        overdue_services = []

        for v in vehicles:
            if v.is_overdue:
                overdue_services.append({
                    'id': str(v.id),
                    'name': v.name,
                    'registration_number': v.registration_number,
                    'next_service_date': str(v.next_service_date),
                    'days_until_service': v.days_until_service,
                })
            elif v.is_upcoming:
                upcoming_services.append({
                    'id': str(v.id),
                    'name': v.name,
                    'registration_number': v.registration_number,
                    'next_service_date': str(v.next_service_date),
                    'days_until_service': v.days_until_service,
                })

        # Sort by days_until_service
        upcoming_services.sort(key=lambda x: x['days_until_service'])
        overdue_services.sort(key=lambda x: x['days_until_service'])

        # Recent vehicles (last 3)
        recent_vehicles = []
        for v in vehicles.order_by('-created_at')[:3]:
            recent_vehicles.append({
                'id': str(v.id),
                'name': v.name,
                'brand': v.brand,
                'registration_number': v.registration_number,
                'last_service_date': str(v.last_service_date),
                'next_service_date': str(v.next_service_date),
                'days_until_service': v.days_until_service,
                'is_overdue': v.is_overdue,
            })

        # Notifications
        unread_notifications = sum(1 for n in Notification.objects.filter(user=user) if not n.is_read)

        vehicle_ids = [v.id for v in vehicles]
        reminder_enabled_count = sum(1 for r in Reminder.objects.filter(vehicle_id__in=vehicle_ids) if r.is_enabled)

        return Response({
            'success': True,
            'dashboard': {
                'total_vehicles': vehicles.count(),
                'upcoming_services_count': len(upcoming_services),
                'overdue_services_count': len(overdue_services),
                'upcoming_services': upcoming_services[:5],
                'overdue_services': overdue_services[:5],
                'recent_vehicles': recent_vehicles,
                'unread_notifications': unread_notifications,
                'reminder_enabled_count': reminder_enabled_count,
            }
        })


class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        today = date.today()
        vehicles = Vehicle.objects.all()

        # Basic stats
        total_users = User.objects.filter(role='customer').count()
        total_vehicles = vehicles.count()
        total_services = ServiceHistory.objects.count()

        upcoming_count = sum(1 for v in vehicles if v.is_upcoming)
        overdue_count = sum(1 for v in vehicles if v.is_overdue)

        # Today's reminders
        todays_reminders = ReminderLog.objects.filter(
            sent_at__date=today, status='sent'
        ).count()

        # Monthly registrations (last 6 months)
        monthly_registrations = []
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            count = User.objects.filter(
                date_joined__year=month_date.year,
                date_joined__month=month_date.month,
                role='customer'
            ).count()
            monthly_registrations.append({
                'month': month_date.strftime('%b %Y'),
                'count': count
            })

        # Monthly services (last 6 months)
        monthly_services = []
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            count = ServiceHistory.objects.filter(
                service_date__year=month_date.year,
                service_date__month=month_date.month
            ).count()
            monthly_services.append({
                'month': month_date.strftime('%b %Y'),
                'count': count
            })

        # Vehicle brands distribution
        brand_distribution = list(
            Vehicle.objects.values('brand')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # Recent activities
        recent_users = User.objects.filter(role='customer').order_by('-date_joined')[:5]
        recent_vehicles = Vehicle.objects.order_by('-created_at')[:5]
        recent_services = ServiceHistory.objects.order_by('-created_at')[:5]

        recent_activities = []
        for u in recent_users:
            recent_activities.append({
                'type': 'user_registered',
                'message': f"New user registered: {u.full_name}",
                'timestamp': u.date_joined.isoformat(),
            })
        for v in recent_vehicles:
            recent_activities.append({
                'type': 'vehicle_added',
                'message': f"Vehicle added: {v.name} ({v.registration_number})",
                'timestamp': v.created_at.isoformat(),
            })
        for s in recent_services:
            recent_activities.append({
                'type': 'service_added',
                'message': f"Service recorded for {s.vehicle.name}",
                'timestamp': s.created_at.isoformat(),
            })

        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)

        # Unread contact messages
        unread_messages = ContactMessage.objects.filter(status='unread').count()

        return Response({
            'success': True,
            'dashboard': {
                'stats': {
                    'total_users': total_users,
                    'total_vehicles': total_vehicles,
                    'total_services': total_services,
                    'upcoming_services': upcoming_count,
                    'overdue_services': overdue_count,
                    'todays_reminders': todays_reminders,
                    'unread_messages': unread_messages,
                },
                'charts': {
                    'monthly_registrations': monthly_registrations,
                    'monthly_services': monthly_services,
                    'brand_distribution': brand_distribution,
                },
                'recent_activities': recent_activities[:10],
            }
        })
