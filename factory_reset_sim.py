import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from finance.treasury_models import Treasury, TreasuryTransfer, TreasuryTransaction, DailyTreasuryReport
from manufacturing.models import Workshop, ManufacturingOrder, ProductionStage
from inventory.models import Carat, Item
from sales.models import Invoice, InvoiceItem

def factory_reset_and_simulate():
    print("!!! STARTING CLEAN FACTORY RESET !!!")
    
    # Secure order of deletion
    try:
        ProductionStage.objects.all().delete()
        ManufacturingOrder.objects.all().delete()
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        Item.objects.all().delete()
        TreasuryTransaction.objects.all().delete()
        TreasuryTransfer.objects.all().delete()
        DailyTreasuryReport.objects.all().delete()
        print("Cleanup Complete.")
    except Exception as e:
        print(f"Cleanup issue: {e}")

    # INITIAL SETUP
    admin_user = User.objects.filter(is_superuser=True).first()
    carat_18, _ = Carat.objects.get_or_create(name="18k", defaults={'purity': 0.750})
    today = timezone.now().date()
    
    # Get Treasuries
    main_treasury = Treasury.objects.get(code='MAIN')
    prod_treasury = Treasury.objects.get(code='PROD_TREASURY')

    # STEP 1: LOAD MAIN TREASURY WITH 200g
    print("\n--- STEP 1: Main Treasury +200g Gold 18k ---")
    TreasuryTransaction.objects.create(
        treasury=main_treasury,
        transaction_type='gold_in',
        gold_weight=Decimal('200.00'),
        gold_carat=carat_18,
        description="رصيد البداية - تجربة تشغيل الـ 200 جرام",
        created_by=admin_user,
        date=today
    )

    # STEP 2: TRANSFER TO PRODUCTION
    print("--- STEP 2: Transfer 200g (Main -> Production) ---")
    TreasuryTransfer.objects.create(
        from_treasury=main_treasury,
        to_treasury=prod_treasury,
        gold_weight=Decimal('200.00'),
        gold_carat=carat_18,
        status='completed',
        initiated_by=admin_user,
        confirmed_by=admin_user,
        notes="DEMO: تسليم عهدة الخام للإنتاج",
        date=today
    )

    # STEP 3: DISTRIBUTE 200g INTO PIECES
    workshop, _ = Workshop.objects.get_or_create(name="ورشة الإنتاج المجمعة", defaults={'workshop_type': 'internal'})
    
    # Distribution Scenario: 15 to Tazga, 30 to Polishing, 155 General
    distributions = [
        ("Tazga Piece", Decimal('15.00'), Decimal('14.85'), "Fadi (Tazga)"),     # 0.15g scrap
        ("Polishing Group", Decimal('30.00'), Decimal('29.65'), "Sami (Polishing)"), # 0.35g scrap
        ("Main Production", Decimal('155.00'), Decimal('153.50'), "Hassan (Master)"),   # 1.50g scrap
    ]

    total_output = Decimal('0.00')
    total_input = Decimal('0.00')
    
    print("\n--- STEP 3: Distribution into Workshop Parts ---")
    for name, in_w, out_w, tech in distributions:
        order = ManufacturingOrder.objects.create(
            order_number=f"PROD-{timezone.now().strftime('%M%S')}-{tech.split()[0]}",
            workshop=workshop,
            carat=carat_18,
            input_weight=in_w,
            output_weight=out_w,
            scrap_weight=in_w - out_w,
            status='completed',
            start_date=today
        )
        
        # Add Stage for visibility
        ProductionStage.objects.create(
            order=order,
            stage_name='casting',
            input_weight=in_w,
            output_weight=out_w,
            technician=tech
        )
        
        total_input += in_w
        total_output += out_w
        print(f"-> {name}: {in_w}g In | Tech: {tech} | Out: {out_w}g | Scrap: {in_w - out_w}g")

    # STEP 4: RETURN ALL FINISHED PIECES TO MAIN TREASURY
    print(f"\n--- STEP 4: Return Productions ({total_output}g) to Main Treasury ---")
    TreasuryTransaction.objects.create(
        treasury=main_treasury,
        transaction_type='finished_goods_in',
        gold_weight=total_output,
        gold_carat=carat_18,
        description=f"استلام إنتاج اليوم (إجمالي {total_output} جم من وردية اليوم)",
        created_by=admin_user,
        date=today
    )

    print("\n--- SYSTEM READY ---")
    print(f"Total Input: {total_input}g")
    print(f"Total Output: {total_output}g")
    print(f"Total Daily Scrap: {total_input - total_output}g")

if __name__ == '__main__':
    factory_reset_and_simulate()
