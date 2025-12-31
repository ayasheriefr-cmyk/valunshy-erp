from django.db import models
from .models import Account
from django.utils.translation import gettext_lazy as _

class FinanceSettings(models.Model):
    """ Singleton model to store default accounting mappings """
    cash_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_cash')
    sales_revenue_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_revenue')
    inventory_gold_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_inventory')
    cost_of_gold_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_cog')
    vat_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_vat')

    class Meta:
        verbose_name = _("Finance Settings")

    def save(self, *args, **kwargs):
        self.pk = 1 # Ensure only one record exists
        super().save(*args, **kwargs)
