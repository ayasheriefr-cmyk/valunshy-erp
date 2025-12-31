from django.apps import AppConfig


class ManufacturingConfig(AppConfig):
    name = 'manufacturing'

    def ready(self):
        import manufacturing.signals

