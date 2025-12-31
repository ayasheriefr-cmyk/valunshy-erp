import os
import django
import sys
from decimal import Decimal
from django.utils import timezone

# Setup Django
sys.path.append(r'c:\Users\COMPU LINE\Desktop\mm\final\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury, TreasuryTransaction
from manufacturing.models import Workshop, ManufacturingOrder
from core.models import Carat

def verify_report_data():
    today = timezone.now().date()
    
    # 1. Ensure Treasury exists
    treasury, _ = Treasury.objects.get_or_create(
        code='MAIN_TEST',
        defaults={'name': 'الخزينة الرئيسية - اختبار', 'treasury_type': 'main'}
    )
    
    # 2. Add Transactions
    TreasuryTransaction.objects.create(
        treasury=treasury,
        transaction_type='cash_in',
        cash_amount=Decimal('5000.00'),
        description='رصيد افتتاحي تجريبي',
        date=today,
        created_by_id=1 # Assuming admin ID 1 exists
    )
    
    # 3. Add Workshop and Orders
    carat_21 = Carat.objects.filter(name='21').first()
    if not carat_21:
        carat_21 = Carat.objects.create(name='21', purity=0.875)
        
    workshop, _ = Workshop.objects.get_or_create(
        name='ورشة السبك والاختبار',
        defaults={'workshop_type': 'internal'}
    )
    
    ts = int(timezone.now().timestamp())
    # Order started today
    ManufacturingOrder.objects.create(
        order_number=f'TEST-ORD-001-{ts}',
        workshop=workshop,
        carat=carat_21,
        input_weight=Decimal('100.000'),
        scrap_weight=Decimal('0.850'), # 0.85% scrap
        status='in_progress',
        start_date=today
    )
    
    ManufacturingOrder.objects.create(
        order_number=f'TEST-ORD-002-{ts}',
        workshop=workshop,
        carat=carat_21,
        input_weight=Decimal('50.000'),
        scrap_weight=Decimal('0.600'), # 1.2% scrap (high)
        status='in_progress',
        start_date=today
    )
    
    print(f"DONE: Created dummy data for {today}")
    print(f"Treasury: {treasury.name}")
    print(f"Workshop: {workshop.name}")
    print(f"Orders created for today.")

if __name__ == "__main__":
    verify_report_data()
