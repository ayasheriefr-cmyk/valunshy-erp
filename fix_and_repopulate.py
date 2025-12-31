import os
import django
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from finance.models import CostCenter, Account, FinanceSettings, JournalEntry, LedgerEntry
from finance.treasury_models import Treasury, TreasuryTransaction, ExpenseVoucher, ReceiptVoucher

def fix_and_repopulate():
    # 1. Clear previous test data to start fresh
    ExpenseVoucher.objects.all().delete()
    ReceiptVoucher.objects.all().delete()
    TreasuryTransaction.objects.all().delete()
    JournalEntry.objects.all().delete()
    LedgerEntry.objects.all().delete()

    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        return

    # 2. Get or Create necessary Accounts
    cash_acc, _ = Account.objects.get_or_create(code="101001", defaults={'name': "صندوق المركز الرئيسي", 'account_type': 'asset'})
    revenue_acc, _ = Account.objects.get_or_create(code="401001", defaults={'name': "إيرادات مبيعات", 'account_type': 'revenue'})
    expense_acc, _ = Account.objects.get_or_create(code="501001", defaults={'name': "مصروفات عامة", 'account_type': 'expense'})

    # 3. Ensure Settings are correct
    settings, _ = FinanceSettings.objects.get_or_create(id=1)
    settings.cash_account = cash_acc
    settings.sales_revenue_account = revenue_acc
    settings.cost_of_gold_account = expense_acc 
    settings.save()

    # 4. Link Treasury to Account
    treasury = Treasury.objects.first()
    if not treasury:
        treasury = Treasury.objects.create(
            name="Main Treasury",
            code="TR001",
            cash_balance=Decimal('100000.00'),
            responsible_user=admin_user
        )
    
    treasury.linked_account = cash_acc
    treasury.save()

    # 5. Ensure Cost Centers
    sales_cc, _ = CostCenter.objects.get_or_create(code="SALES", defaults={'name': "قسم المبيعات"})
    prod_cc, _ = CostCenter.objects.get_or_create(code="PROD", defaults={'name': "قسم التصنيع والورش"})
    admin_cc, _ = CostCenter.objects.get_or_create(code="ADMIN", defaults={'name': "الإدارة العامة"})

    # 6. Create sample vouchers
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
            ExpenseVoucher.objects.create(
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
        else:
            ReceiptVoucher.objects.create(
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

if __name__ == "__main__":
    fix_and_repopulate()
    print("Done")
