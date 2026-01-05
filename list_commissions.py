import os
import django
import sys

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from sales.models import SalesRepTransaction

transactions = SalesRepTransaction.objects.filter(transaction_type='commission')
print(f"Commission Transactions (Total: {transactions.count()}):")
for t in transactions:
    print(f" - ID: {t.id}, Amount: {t.amount}, Notes: {t.notes}")

print("\nEnd of list.")
