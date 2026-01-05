import os
import django
import sys

# Set default encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from finance.treasury_models import ExpenseVoucher, TreasuryTransaction
from finance.models import LedgerEntry

vouchers = ExpenseVoucher.objects.exclude(status='draft')
print(f"Expense Vouchers (Total: {vouchers.count()}):")
for v in vouchers:
    print(f" - {v.voucher_number}: {v.beneficiary_name}, Amount: {v.amount}, Status: {v.status}, Category: {v.expense_category}")
    
    # Find associated TreasuryTransaction
    trxs = TreasuryTransaction.objects.filter(reference_type='expense_voucher', reference_id=v.id)
    for trx in trxs:
        print(f"   -> TreasuryTransaction {trx.id}: {trx.transaction_type}, Amount: {trx.cash_amount}")
        
        # Find associated GL entries
        entries = LedgerEntry.objects.filter(journal_entry__reference=f"TRX-{trx.id}")
        for ent in entries:
            print(f"      - GL Account: {ent.account.code} ({ent.account.name}), Debit: {ent.debit}, Credit: {ent.credit}")

print("\nEnd of inspection.")
