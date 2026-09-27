from django.apps import AppConfig


class KitchinesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kitchines'

    def ready(self):
        from . import signals  # noqa: F401
