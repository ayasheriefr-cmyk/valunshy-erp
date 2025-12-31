import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.models import Account, FinanceSettings
from finance.treasury_models import Treasury

def link_all_treasuries():
    settings = FinanceSettings.objects.first()
    if not settings or not settings.cash_account:
        print("Error: Cash account not set in FinanceSettings.")
        return

    default_acc = settings.cash_account
    
    treasuries = Treasury.objects.filter(linked_account=None)
    for t in treasuries:
        t.linked_account = default_acc
        t.save()
        print(f"Linked Treasury {t.id} ({t.code}) to Account {default_acc.id}")

if __name__ == "__main__":
    link_all_treasuries()
