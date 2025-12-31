import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import ExpenseVoucher, ReceiptVoucher
from django.db.models import Q

def check_vouchers():
    print("--- Searching Expense Vouchers ---")
    expenses = ExpenseVoucher.objects.filter(Q(description__icontains='ورشة') | Q(notes__icontains='ورشة'))
    print(f"Found {expenses.count()} expenses.")
    for e in expenses:
        print(f"Voucher: {e.voucher_number} | Amount: {e.amount} | Desc: {e.description}")

    print("\n--- Searching Receipt Vouchers ---")
    receipts = ReceiptVoucher.objects.filter(Q(description__icontains='ورشة') | Q(notes__icontains='ورشة'))
    print(f"Found {receipts.count()} receipts.")
    for r in receipts:
        print(f"Voucher: {r.voucher_number} | Amount: {r.amount} | Desc: {r.description}")

if __name__ == "__main__":
    check_vouchers()
