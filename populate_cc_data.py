import os
import django
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from finance.models import CostCenter, Account, FinanceSettings
from finance.treasury_models import Treasury, ExpenseVoucher, ReceiptVoucher

def populate_cost_center_data():
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No admin user found.")
        return

    # 1. Ensure we have Cost Centers
    sales_cc, _ = CostCenter.objects.get_or_create(code="SALES", defaults={'name': "قسم المبيعات"})
    prod_cc, _ = CostCenter.objects.get_or_create(code="PROD", defaults={'name': "قسم التصنيع والورش"})
    admin_cc, _ = CostCenter.objects.get_or_create(code="ADMIN", defaults={'name': "الإدارة العامة"})

    # 2. Ensure Treasury
    treasury = Treasury.objects.first()
    if not treasury:
        print("No treasury found. Please create one first.")
        return

    # 3. Create sample expenses (Paid)
    vouchers = [
        {
            'type': 'expense',
            'beneficiary': 'مورد أدوات',
            'amount': Decimal('1500.00'),
            'cc': prod_cc,
            'desc': 'شراء مستلزمات ورشة'
        },
        {
            'type': 'expense',
            'beneficiary': 'شركة كهرباء',
            'amount': Decimal('800.00'),
            'cc': admin_cc,
            'desc': 'فاتورة كهرباء المكتب'
        },
        {
            'type': 'receipt',
            'payer': 'عميل تجزئة',
            'amount': Decimal('5000.00'),
            'cc': sales_cc,
            'desc': 'مبيعات نقدية'
        }
    ]

    for v in vouchers:
        if v['type'] == 'expense':
            voucher = ExpenseVoucher.objects.create(
                voucher_type='expense',
                status='paid',
                treasury=treasury,
                beneficiary_name=v['beneficiary'],
                amount=v['amount'],
                cost_center=v['cc'],
                description=v['desc'],
                requested_by=admin_user,
                paid_by=admin_user,
                date=timezone.now().date(),
                paid_date=timezone.now().date()
            )
            print(f"Created Expense Voucher: {voucher.voucher_number}")
        else:
            voucher = ReceiptVoucher.objects.create(
                voucher_type='collection',
                status='confirmed',
                treasury=treasury,
                payer_name=v['payer'],
                cash_amount=v['amount'],
                cost_center=v['cc'],
                description=v['desc'],
                received_by=admin_user,
                date=timezone.now().date()
            )
            print(f"Created Receipt Voucher: {voucher.voucher_number}")

if __name__ == "__main__":
    populate_cost_center_data()
