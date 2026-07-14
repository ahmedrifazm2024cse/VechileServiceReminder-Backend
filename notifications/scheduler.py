"""
APScheduler - Automatic Reminder Scheduler
Runs every day at 8:00 AM to send service reminder emails
"""

import logging
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_service_reminders():
    """
    Main scheduler job - runs daily at 8:00 AM.
    Checks all vehicles with reminders enabled and sends emails
    when service is due within the configured reminder days.
    """
    from vehicles.models import Vehicle
    from notifications.models import Reminder, ReminderLog, Notification

    logger.info("Running daily service reminder check...")
    today = date.today()
    sent_count = 0
    failed_count = 0

    # Get all vehicles with reminders enabled
    reminders = Reminder.objects.filter(is_enabled=True).select_related(
        'vehicle', 'vehicle__owner'
    )

    for reminder in reminders:
        vehicle = reminder.vehicle
        user = vehicle.owner
        next_service = vehicle.next_service_date
        days_until = (next_service - today).days

        # Check if any reminder day matches
        for reminder_day in reminder.reminder_days:
            if days_until == reminder_day:
                # Check for duplicate - already sent this reminder today
                already_sent = ReminderLog.objects.filter(
                    vehicle=vehicle,
                    reminder_days=reminder_day,
                    service_due_date=next_service,
                    status='sent'
                ).exists()

                if already_sent:
                    logger.info(f"Skipping duplicate reminder for {vehicle.name} ({reminder_day} days)")
                    continue

                # Send reminder email
                try:
                    _send_reminder_email(user, vehicle, next_service, days_until)

                    # Log success
                    ReminderLog.objects.create(
                        vehicle=vehicle,
                        user=user,
                        email_sent_to=user.email,
                        reminder_days=reminder_day,
                        service_due_date=next_service,
                        status='sent'
                    )

                    # Create in-app notification
                    Notification.objects.create(
                        user=user,
                        title=f"Service Reminder: {vehicle.name}",
                        message=f"Your vehicle {vehicle.name} ({vehicle.registration_number}) "
                                f"is due for service in {days_until} days on {next_service}.",
                        notification_type='reminder',
                        related_vehicle=vehicle
                    )

                    sent_count += 1
                    logger.info(f"Reminder sent to {user.email} for vehicle {vehicle.name}")

                except Exception as e:
                    ReminderLog.objects.create(
                        vehicle=vehicle,
                        user=user,
                        email_sent_to=user.email,
                        reminder_days=reminder_day,
                        service_due_date=next_service,
                        status='failed',
                        error_message=str(e)
                    )
                    failed_count += 1
                    logger.error(f"Failed to send reminder for {vehicle.name}: {e}")

    # Also check for overdue vehicles
    _check_overdue_reminders()

    logger.info(f"Reminder check complete. Sent: {sent_count}, Failed: {failed_count}")


def _send_reminder_email(user, vehicle, service_date, days_until):
    """Send a reminder email to the user."""
    subject = f"Vehicle Service Reminder - {vehicle.name}"

    try:
        html_message = render_to_string('emails/service_reminder.html', {
            'user': user,
            'vehicle': vehicle,
            'service_date': service_date,
            'days_until': days_until,
            'app_name': settings.APP_NAME,
            'frontend_url': settings.FRONTEND_URL,
        })
    except Exception:
        html_message = None

    plain_message = f"""
Hello {user.full_name},

Your vehicle requires servicing soon!

Vehicle Name: {vehicle.name}
Registration Number: {vehicle.registration_number}
Service Due Date: {service_date}
Days Remaining: {days_until} days

Please schedule your service appointment at the earliest.

Thank you,
{settings.APP_NAME}
"""

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def _check_overdue_reminders():
    """Create notifications for overdue vehicles."""
    from vehicles.models import Vehicle
    from notifications.models import Notification

    today = date.today()
    overdue_vehicles = []

    for vehicle in Vehicle.objects.filter(reminder__is_enabled=True).select_related('owner', 'reminder'):
        if vehicle.is_overdue:
            # Check if we already sent overdue notification today
            already_notified = Notification.objects.filter(
                user=vehicle.owner,
                related_vehicle=vehicle,
                notification_type='overdue',
                created_at__date=today
            ).exists()

            if not already_notified:
                Notification.objects.create(
                    user=vehicle.owner,
                    title=f"Service Overdue: {vehicle.name}",
                    message=f"Your vehicle {vehicle.name} ({vehicle.registration_number}) "
                            f"service is overdue! Last service was on {vehicle.last_service_date}.",
                    notification_type='overdue',
                    related_vehicle=vehicle
                )


def start_scheduler():
    """Initialize and start the APScheduler."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from django.conf import settings

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            send_service_reminders,
            trigger=CronTrigger(hour=8, minute=0),  # Every day at 8:00 AM
            id='daily_service_reminder',
            name='Daily Service Reminder',
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler started. Daily reminders scheduled at 8:00 AM.")
        return scheduler
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        return None
