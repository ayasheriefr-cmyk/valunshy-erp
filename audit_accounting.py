import os
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.models import Account, FinanceSettings, JournalEntry, LedgerEntry
from finance.treasury_models import Treasury, TreasuryTransaction, ExpenseVoucher, ReceiptVoucher

def run_system_audit():
    print("--- Accounting System Audit ---\n")
    
    # 1. Audit Finance Settings
    print("1. Finance Settings Check:")
    settings = FinanceSettings.objects.first()
    if not settings:
        print("[!] ERROR: No FinanceSettings found. Systems will fail to post journal entries.")
    else:
        fields = ['cash_account', 'sales_revenue_account', 'inventory_gold_account', 'cost_of_gold_account', 'vat_account']
        for field in fields:
            acc = getattr(settings, field)
            if not acc:
                print(f"[!] WARNING: {field} is NOT mapped.")
            else:
                print(f"[OK] {field} is mapped to ID: {acc.id} (Code: {acc.code})")
    
    # 2. Audit Treasuries
    print("\n2. Treasury Linkage Check:")
    treasuries = Treasury.objects.all()
    if not treasuries.exists():
        print("[!] No treasuries found.")
    else:
        for t in treasuries:
            if not t.linked_account:
                print(f"[!] ERROR: Treasury ID {t.id} (Code: {t.code}) is NOT linked to a GL account.")
            else:
                print(f"[OK] Treasury ID {t.id} linked to account ID: {t.linked_account_id}")
    
    # 3. Data Integrity Check (Orphaned Transactions)
    print("\n3. Data Flow Integrity:")
    trx_count = TreasuryTransaction.objects.count()
    journals_count = JournalEntry.objects.filter(reference__startswith='TRX-').count()
    
    print(f"Total Treasury Transactions: {trx_count}")
    print(f"Auto-Journal Entries found: {journals_count}")
    
    if trx_count > 0 and journals_count < trx_count:
        print(f"[!] WARNING: Potential mismatch. {trx_count - journals_count} transactions might not have journal entries.")
        # Check specific orphans
        for trx in TreasuryTransaction.objects.all():
            ref = f"TRX-{trx.id}"
            if not JournalEntry.objects.filter(reference=ref).exists():
                print(f"  [-] Orphaned Transaction: ID {trx.id} ({trx.reference_type})")

    # 4. Cost Center Check
    print("\n4. Cost Center Integrity:")
    le_total = LedgerEntry.objects.count()
    le_with_cc = LedgerEntry.objects.exclude(cost_center=None).count()
    print(f"Total Ledger Entries: {le_total}")
    print(f"Ledger Entries with Cost Center: {le_with_cc}")

if __name__ == "__main__":
    run_system_audit()
