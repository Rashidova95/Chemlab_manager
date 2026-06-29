from django.apps import AppConfig


class SamplesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.samples'

    def ready(self):
        import apps.samples.signals