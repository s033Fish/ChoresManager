from django.apps import AppConfig


class ChoresManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chores_manager"
    
    def ready(self):
        import chores_manager.signals  # Import your signals module here
