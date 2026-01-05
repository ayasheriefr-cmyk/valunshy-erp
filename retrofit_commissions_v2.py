import os
import django
import sys
import re

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from sales.models import SalesRepTransaction, Invoice
from finance.models import JournalEntry, LedgerEntry, Account
from decimal import Decimal

transactions = SalesRepTransaction.objects.filter(transaction_type='commission')
print(f"Retrofitting {transactions.count()} commission transactions...")

expense_acc = Account.objects.get(code='5303')
payable_acc = Account.objects.get(code='2102')

for t in transactions:
    if t.invoice:
        inv = t.invoice
    else:
        # Try to find invoice number in notes
        # Examples: "INV-MOB-77347", "SALE-TEST-001"
        match = re.search(r'(INV-MOB-\d+|SALE-TEST-\d+|TEST-INV-\d+)', t.notes)
        if match:
            inv_num = match.group(1)
            inv = Invoice.objects.filter(invoice_number=inv_num).first()
            if inv:
                t.invoice = inv
                t.save(update_fields=['invoice'])
                print(f" - Linked transaction {t.id} to invoice {inv_num}")
            else:
                print(f" - Invoice {inv_num} not found for transaction {t.id}")
                continue
        else:
            print(f" - Could not find invoice number in notes: '{t.notes}'")
            continue
            
    ref = f"COMM-{inv.invoice_number}"
    if not JournalEntry.objects.filter(reference=ref).exists():
        if t.amount > 0:
            print(f" - Posting commission for invoice {inv.invoice_number} ({t.amount})")
            
            journal = JournalEntry.objects.create(
                reference=ref,
                description=f"استحقاق عمولة مندوب - {t.sales_rep.name} - فاتورة {inv.invoice_number}",
                date=inv.created_at.date()
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
            print(f" - Skipping zero amount commission for invoice {inv.invoice_number}")
    else:
        print(f" - Commission for {inv.invoice_number} already posted.")

print("Retrofit complete.")
