from django.apps import AppConfig


class FinanceConfig(AppConfig):
    name = 'finance'
    verbose_name = "الإدارة المالية"

    def ready(self):
        import finance.signals
