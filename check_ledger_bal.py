import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.models import LedgerEntry, Account
from django.db.models import Sum

def check_ledger():
    print("--- Searching Ledger for Workshops ---")
    workshop_accounts = Account.objects.filter(name__icontains='ورشة')
    if not workshop_accounts.exists():
        print("No accounts with 'ورشة' in name.")
    
    for acc in workshop_accounts:
        bal = LedgerEntry.objects.filter(account=acc).aggregate(
            total=Sum('credit') - Sum('debit')
        )['total'] or 0
        print(f"Account: {acc.name:20} | Balance: {bal:10.2f}")

    print("\n--- Searching for Labor Accounts ---")
    labor_accounts = Account.objects.filter(name__icontains='مصنعية')
    for acc in labor_accounts:
        bal = LedgerEntry.objects.filter(account=acc).aggregate(
            total=Sum('credit') - Sum('debit')
        )['total'] or 0
        print(f"Account: {acc.name:20} | Balance: {bal:10.2f}")

if __name__ == "__main__":
    check_ledger()
