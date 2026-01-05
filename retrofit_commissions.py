import os
import django
import sys

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from sales.models import SalesRepTransaction
from finance.models import JournalEntry, LedgerEntry, Account
from decimal import Decimal

transactions = SalesRepTransaction.objects.filter(transaction_type='commission')
print(f"Retrofitting {transactions.count()} commission transactions...")

expense_acc = Account.objects.get(code='5303')
payable_acc = Account.objects.get(code='2102')

for t in transactions:
    if not t.invoice:
        print(f" - Skipping transaction {t.id} (No invoice linked)")
        continue
        
    ref = f"COMM-{t.invoice.invoice_number}"
    if not JournalEntry.objects.filter(reference=ref).exists():
        print(f" - Posting commission for invoice {t.invoice.invoice_number} ({t.amount})")
        
        journal = JournalEntry.objects.create(
            reference=ref,
            description=f"استحقاق عمولة مندوب - {t.sales_rep.name} - فاتورة {t.invoice.invoice_number}",
            date=t.invoice.created_at.date()
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
        print(f" - Commission for {t.invoice.invoice_number} already posted.")

print("Retrofit complete.")
