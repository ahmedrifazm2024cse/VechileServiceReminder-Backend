from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        """Start the scheduler when the app is ready."""
        import os
        # Only start scheduler in the main process, not in reloader or management commands
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        try:
            from .scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not start scheduler: {e}")
