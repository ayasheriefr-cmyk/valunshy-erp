import os
import django
import sys
from decimal import Decimal

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from sales.models import SalesRepTransaction
from finance.models import JournalEntry, LedgerEntry, Account

transactions = SalesRepTransaction.objects.filter(transaction_type='commission')
print(f"Retrofitting {transactions.count()} commission transactions...")

expense_acc = Account.objects.get(code='5303')
payable_acc = Account.objects.get(code='2102')

for t in transactions:
    # Use ID for reference since invoice is missing
    ref = f"COMM-HIST-{t.id}"
    if not JournalEntry.objects.filter(reference=ref).exists():
        if t.amount > 0:
            print(f" - Posting historical commission ID {t.id} ({t.amount}) on {t.created_at.date()}")
            
            journal = JournalEntry.objects.create(
                reference=ref,
                description=f"استحقاق عمولة مندوب (تاريخي) - {t.sales_rep.name} - {t.notes}",
                date=t.created_at.date()
            )
            
            # Debit: Expense
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=expense_acc,
                debit=t.amount,
                credit=0
            )
            
            # Credit: Payable
            LedgerEntry.objects.create(
                journal_entry=journal,
                account=payable_acc,
                debit=0,
                credit=t.amount
            )
        else:
            print(f" - Skipping zero amount historical commission ID {t.id}")
    else:
        print(f" - Historical commission ID {t.id} already posted.")

print("Retrofit complete.")
