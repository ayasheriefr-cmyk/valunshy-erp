import os
import django
import sys
from decimal import Decimal
from django.utils import timezone

# Setup Django
sys.path.append(r'c:\Users\COMPU LINE\Desktop\mm\final\gold')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury, TreasuryTransaction, TreasuryTransfer
from manufacturing.models import Workshop, ManufacturingOrder, WorkshopTransfer
from core.models import Carat
from django.contrib.auth.models import User

def setup_scenario():
    today = timezone.now().date()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    # 1. Clean data for today
    TreasuryTransaction.objects.filter(date=today).delete()
    ManufacturingOrder.objects.filter(start_date=today).delete()
    WorkshopTransfer.objects.filter(date=today).delete()
    TreasuryTransfer.objects.filter(date=today).delete()
    
    print("DONE: Cleaned today's data.")
    
    # 2. Setup Treasuries
    main_treasury, _ = Treasury.objects.get_or_create(
        code='MAIN',
        defaults={'name': 'الخزينة الرئيسية', 'treasury_type': 'main'}
    )
    prod_treasury, _ = Treasury.objects.get_or_create(
        code='PROD_TREASURY',
        defaults={'name': 'خزينة الإنتاج', 'treasury_type': 'production'}
    )
    
    # 3. Setup Workshops
    workshop_1, _ = Workshop.objects.get_or_create(
        name='ورشة التشكيل',
        defaults={'workshop_type': 'internal'}
    )
    laser_workshop, _ = Workshop.objects.get_or_create(
        name='ورشة الليزر',
        defaults={'workshop_type': 'internal'}
    )
    
    carat_18 = Carat.objects.filter(name='18').first()
    if not carat_18:
        carat_18 = Carat.objects.create(name='18', purity=0.750)
        
    ts = int(timezone.now().timestamp())

    # 4. SCENARIO: Main Treasury -> Production Treasury (500g)
    TreasuryTransfer.objects.create(
        from_treasury=main_treasury,
        to_treasury=prod_treasury,
        cash_amount=0,
        gold_weight=Decimal('500.000'),
        gold_carat=carat_18,
        notes='تحويل عهدة ذهب لإنتاج اليوم',
        date=today,
        initiated_by=admin_user,
        confirmed_by=admin_user,
        status='completed'
    )
    # TreasuryTransfer automatically creates transactions if its save method is set up that way, 
    # but to be safe and given the current state, we'll let the view handle it.
    # Note: If TreasuryTransfer.save() creates transactions, we might get duplicates. 
    # Let's check common logic or assume we need to create them if not automatic.

    # 5. SCENARIO: Production Treasury -> Workshop 1 (200g)
    # Order 1: High Scrap (8%)
    ManufacturingOrder.objects.create(
        order_number=f'HIGH-SCRAP-{ts}',
        workshop=workshop_1,
        carat=carat_18,
        input_weight=Decimal('100.000'),
        scrap_weight=Decimal('8.000'),
        status='in_progress',
        start_date=today
    )
    
    # Order 2: Normal Scrap (0.5%)
    ManufacturingOrder.objects.create(
        order_number=f'NORMAL-SCRAP-{ts}',
        workshop=workshop_1,
        carat=carat_18,
        input_weight=Decimal('100.000'),
        scrap_weight=Decimal('0.500'),
        status='in_progress',
        start_date=today
    )

    # 6. SCENARIO: Workshop -> Laser -> Workshop
    WorkshopTransfer.objects.create(
        transfer_number=f'W-LASER-{ts}',
        from_workshop=workshop_1,
        to_workshop=laser_workshop,
        carat=carat_18,
        weight=Decimal('50.000'),
        status='completed',
        initiated_by=admin_user,
        date=today
    )
    WorkshopTransfer.objects.create(
        transfer_number=f'LASER-W-{ts}',
        from_workshop=laser_workshop,
        to_workshop=workshop_1,
        carat=carat_18,
        weight=Decimal('50.000'),
        status='completed',
        initiated_by=admin_user,
        date=today
    )

    # 7. Final Handover: Prod Treasury -> Main Treasury (Remaining)
    # Assuming some work stayed in workshops, hand back 250g
    TreasuryTransfer.objects.create(
        from_treasury=prod_treasury,
        to_treasury=main_treasury,
        cash_amount=0,
        gold_weight=Decimal('250.000'),
        gold_carat=carat_18,
        notes='تسليم متبقي العهدة والإنتاج للخزينة الرئيسية',
        date=today,
        initiated_by=admin_user,
        confirmed_by=admin_user,
        status='completed'
    )

    print("DONE: Complex scenario setup completed.")

if __name__ == "__main__":
    setup_scenario()
