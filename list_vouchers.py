import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import ExpenseVoucher, ReceiptVoucher

def list_vouchers():
    print("--- All Expense Vouchers ---")
    expenses = ExpenseVoucher.objects.all()
    print(f"Total: {expenses.count()}")
    for e in expenses:
        print(f"No: {e.voucher_number} | Amount: {e.amount} | Desc: {e.description} | Ben: {e.beneficiary_name}")

    print("\n--- All Receipt Vouchers ---")
    receipts = ReceiptVoucher.objects.all()
    print(f"Total: {receipts.count()}")
    for r in receipts:
        # Check fields for ReceiptVoucher too
        print(f"No: {r.voucher_number} | Amount: {r.amount} | Desc: {r.description}")

if __name__ == "__main__":
    list_vouchers()
