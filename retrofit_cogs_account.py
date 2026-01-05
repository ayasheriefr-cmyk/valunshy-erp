import os
import django
import sys

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from finance.models import FinanceSettings, LedgerEntry, Account
from sales.models import Invoice

settings = FinanceSettings.objects.first()
correct_cogs_acc = settings.cost_of_gold_account # This is now 5101
old_cogs_acc_code = '501001'

print(f"Correct COGS Account: {correct_cogs_acc.code} - {correct_cogs_acc.name}")

# Find ledger entries for confirmed invoices that are using the old account
invs = Invoice.objects.filter(status='confirmed')
for inv in invs:
    entries = LedgerEntry.objects.filter(
        journal_entry__reference=inv.invoice_number,
        account__code=old_cogs_acc_code
    )
    if entries.exists():
        print(f"Fixing entries for invoice {inv.invoice_number}:")
        for ent in entries:
            old_code = ent.account.code
            ent.account = correct_cogs_acc
            ent.save()
            print(f" - Moved entry from {old_code} to {ent.account.code}")
    else:
        # Check if it even HAS COGS entries at all
        je = JournalEntry.objects.filter(reference=inv.invoice_number).first()
        if je:
            has_cog = je.ledger_entries.filter(account=correct_cogs_acc).exists()
            if not has_cog:
                print(f"Invoice {inv.invoice_number} is missing COGS entries entirely. Adding them...")
                # ... reuse logic from verify_cogs.py ...
                total_cogs = sum(item.total_cost for item in inv.items.all())
                total_weight = sum(item.sold_weight for item in inv.items.all())
                
                if total_cogs > 0:
                    LedgerEntry.objects.create(
                        journal_entry=je,
                        account=correct_cogs_acc,
                        debit=total_cogs,
                        credit=0
                    )
                    LedgerEntry.objects.create(
                        journal_entry=je,
                        account=settings.inventory_gold_account,
                        debit=0,
                        credit=total_cogs,
                        gold_credit=total_weight
                    )
                    print(f" - Added COGS and Inventory entries.")

from finance.models import JournalEntry
print("Cleanup and Refit complete.")
