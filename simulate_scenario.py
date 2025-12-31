import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from finance.treasury_models import Treasury, TreasuryTransfer, TreasuryTransaction
from manufacturing.models import Workshop, ManufacturingOrder, ProductionStage
from inventory.models import Carat

def run_clean_scenario():
    print("Starting Workflow Simulation: 200g Gold Production Scenario (Realistic)")
    
    admin_user = User.objects.filter(is_superuser=True).first()
    carat_18, _ = Carat.objects.get_or_create(name="18k", defaults={'purity': 0.750})
    
    # 1. CLEANUP PREVIOUS MOKS FOR TODAY
    today = timezone.now().date()
    TreasuryTransaction.objects.filter(date=today, description__icontains="DEMO").delete()
    TreasuryTransfer.objects.filter(date=today, notes__icontains="DEMO").delete()
    ManufacturingOrder.objects.filter(start_date=today, order_number__icontains="DEMO").delete()

    # IDs for MAIN and PROD
    MAIN_ID = 1
    PROD_ID = 7 
    
    try:
        main_treasury = Treasury.objects.get(id=MAIN_ID)
        prod_treasury = Treasury.objects.get(id=PROD_ID)
    except:
        print("Required Treasuries (1 or 7) not found.")
        return

    # 2. Step 1: Transfer from Main to Production (200g - Total Handover)
    # This represents the material moving from the safe to the Production Manager's custody.
    print("\n--- Step 1: Bulk Transfer (Main -> Production) ---")
    TreasuryTransfer.objects.create(
        from_treasury=main_treasury,
        to_treasury=prod_treasury,
        cash_amount=Decimal('0.00'),
        gold_weight=Decimal('200.00'),
        gold_carat=carat_18,
        status='completed',
        initiated_by=admin_user,
        confirmed_by=admin_user,
        notes="DEMO: تسليم إجمالي الخام للإنتاج (200 جم)",
        date=today
    )
    
    # 3. Step 2: Distribution to Stages (Realistic Scrap: 2g total)
    # Distribution doesn't have to be one workshop. The order can pass through technicians.
    workshop, _ = Workshop.objects.get_or_create(name="ورشة الإنتاج المجمعة", defaults={'workshop_type': 'internal'})
    
    order = ManufacturingOrder.objects.create(
        order_number=f"DEMO-REAL-{timezone.now().strftime('%M%S')}",
        workshop=workshop,
        carat=carat_18,
        input_weight=Decimal('200.00'),
        status='completed', # Marking as completed after stages
        start_date=today
    )
    
    # Realistic Stages showing the gold moving through the factory
    # Total loss: 2.0g
    stages_data = [
        ('casting', Decimal('200.00'), Decimal('199.30'), "Ahmad (Caster)"),     # 0.7g loss
        ('filing', Decimal('199.30'), Decimal('198.80'), "Moussa (Filer)"),     # 0.5g loss
        ('polishing', Decimal('198.80'), Decimal('198.00'), "Kamal (Polisher)") # 0.8g loss
    ]
    
    for stage_code, in_w, out_w, tech in stages_data:
        ProductionStage.objects.create(
            order=order,
            stage_name=stage_code,
            input_weight=in_w,
            output_weight=out_w,
            technician=tech
        )
        print(f"Stage Done: {stage_code} | {in_w}g -> {out_w}g | Tech: {tech}")

    # Finalize Order
    order.output_weight = Decimal('198.00')
    order.scrap_weight = Decimal('2.00') # 200 - 198 = 2g total scrap
    order.save()
    
    # 4. Step 3: Return Finished Parts to Main Treasury
    print("\n--- Step 3: Finished Goods Return (Production -> Main) ---")
    TreasuryTransaction.objects.create(
        treasury=main_treasury,
        transaction_type='finished_goods_in',
        gold_weight=Decimal('198.00'),
        gold_carat=carat_18,
        description=f"DEMO: استلام قطع ذهب جاهزة عيار 18 (أمر {order.order_number})",
        created_by=admin_user,
        date=today
    )
    
    print("\nSUCCESS: Simulated 200g Transfer -> Production Flow -> 198g Return (2g Scrap).")

if __name__ == '__main__':
    run_clean_scenario()
