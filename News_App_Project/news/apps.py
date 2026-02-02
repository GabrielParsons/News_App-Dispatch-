from django.apps import AppConfig


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'
    
    def ready(self):
        """
        Import signals when the app is ready.
        This ensures signal handlers are registered.
        """
        import news.signals  # noqa

