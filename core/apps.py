from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """
        Initialize app settings and signal handlers
        """
        # Import signal handlers if needed
        # from . import signals
        pass
