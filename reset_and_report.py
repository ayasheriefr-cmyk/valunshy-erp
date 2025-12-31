import os
import sys
import django
from django.db.models import Sum
from datetime import date
from decimal import Decimal

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, Workshop, WorkshopSettlement, WorkshopTransfer, Stone
from sales.models import Invoice
from finance.treasury_models import Treasury, TreasuryTransaction, TreasuryTransfer, DailyTreasuryReport, ExpenseVoucher, ReceiptVoucher
from inventory.models import Item, RawMaterial
from finance.models import Account, JournalEntry, OpeningBalance

def run():
    print("Starting FULL SYSTEM ZEROING (Except Main Treasury Gold 18)...")
    
    # 1. Zeroing Inventory (Finished Goods, Raw Materials, Stones)
    print("   - Deleting ALL Finished Items...")
    Item.objects.all().delete()
    
    print("   - Zeroing Raw Materials...")
    RawMaterial.objects.update(current_weight=0)
    
    print("   - Zeroing Stones...")
    Stone.objects.update(current_stock=0)

    # 2. Deleting Manufacturing Orders
    print("   - Cleaning Manufacturing Orders...")
    ManufacturingOrder.objects.all().delete()

    # 3. Deleting Sales
    print("   - Deleting ALL Sales Invoices...")
    Invoice.objects.all().delete()

    # 4. Deleting Financial Documents
    print("   - Deleting Expense Vouchers...")
    ExpenseVoucher.objects.all().delete()
    
    print("   - Deleting Receipt Vouchers...")
    ReceiptVoucher.objects.all().delete()
    
    print("   - Deleting Daily Treasury Reports...")
    DailyTreasuryReport.objects.all().delete()

    # 5. Clearing Treasury Transactions & Transfers
    print("   - Deleting ALL Treasury Transactions...")
    TreasuryTransaction.objects.all().delete()
    
    print("   - Deleting ALL Treasury Transfers...")
    TreasuryTransfer.objects.all().delete()

    # 6. Cleaning Manufacturing Financials
    print("   - Deleting Workshop Transfers & Settlements...")
    WorkshopTransfer.objects.all().delete()
    WorkshopSettlement.objects.all().delete()
    
    # 7. Zeroing Balances (Treasuries & Workshops)
    print("   - Zeroing ALL Treasury Balances...")
    # First set all to 0
    Treasury.objects.update(
        cash_balance=0,
        gold_balance_18=0,
        gold_balance_21=0,
        gold_balance_24=0,
        gold_casting_balance=0,
        stones_balance=0
    )
    
    # NOW: Set Main Treasury Gold 18 to 399.25
    main_treasury = Treasury.objects.first() 
    if not main_treasury:
        try:
            main_treasury = Treasury.objects.get(id=1)
        except:
             main_treasury = Treasury.objects.filter(is_active=True).first()

    if main_treasury:
        # Use simple string to avoid unicode error
        print(f"   - Setting Main Treasury Gold 18 to 399.25")
        main_treasury.gold_balance_18 = Decimal('399.25')
        main_treasury.save()
    
    print("   - Zeroing ALL Workshop Balances...")
    Workshop.objects.update(
        gold_balance_18=0,
        gold_balance_21=0,
        gold_balance_24=0,
        labor_balance=0,
        filings_balance_18=0,
        filings_balance_21=0,
        filings_balance_24=0
    )
    
    # 8. NEW: Zeroing Accounting Ledger (The 'Financial Dashboard' Source)
    print("   - Deleting ALL Journal Entries (General Ledger)...")
    JournalEntry.objects.all().delete() # Cascades to LedgerEntry
    
    print("   - Deleting Opening Balances...")
    OpeningBalance.objects.all().delete()
    
    print("   - Resetting Account Balances to 0...")
    Account.objects.update(balance=0, gold_balance=0)
    
    # If we want the 399.25 to reflect in Accounting, update Asset Account.
    if main_treasury:
        gold_account = Account.objects.filter(name__icontains='نقدية ذهب').first() or \
                       Account.objects.filter(name__icontains='مخزون ذهب').first()
        if gold_account:
             print(f"   - Updating Accounting Entry for Gold to match 399.25")
             gold_account.gold_balance = Decimal('399.25')
             gold_account.save()

    print("SYSTEM ZEROED SUCCESSFULLY. Main Treasury Gold 18 = 399.25")

if __name__ == '__main__':
    run()
