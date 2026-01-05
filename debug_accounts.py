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
print(f"COGS Account: {settings.cost_of_gold_account}")
print(f"Inventory Account: {settings.inventory_gold_account}")

if settings.cost_of_gold_account:
    print(f" - COGS Code: {settings.cost_of_gold_account.code}")
    print(f" - COGS Type: {settings.cost_of_gold_account.account_type}")

inv = Invoice.objects.filter(invoice_number='TEST-INV-001').first()
if inv:
    print(f"Invoice {inv.invoice_number} ledger entries:")
    entries = LedgerEntry.objects.filter(journal_entry__reference=inv.invoice_number)
    for ent in entries:
        print(f" - Account: {ent.account.code} ({ent.account.name}), Debit: {ent.debit}, Credit: {ent.credit}")
else:
    print("TEST-INV-001 not found.")
