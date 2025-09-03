from django.apps import AppConfig


class HaberdasheryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'haberdashery'
    
    def ready(self):
        import haberdashery.signals
