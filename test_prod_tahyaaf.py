import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from finance.treasury_models import Treasury, TreasuryTransfer, TreasuryTransaction, DailyTreasuryReport
from manufacturing.models import Workshop, ManufacturingOrder, ProductionStage, Stone
from inventory.models import Carat, Item
from sales.models import Invoice, InvoiceItem

def test_tahyaaf_in_production():
    print("!!! TESTING PRODUCTION TAHYAAF (200g DISTRIBUTED WITH STONES) !!!")
    
    # SETUP
    admin_user = User.objects.filter(is_superuser=True).first()
    carat_18, _ = Carat.objects.get_or_create(name="18k", defaults={'purity': 0.750})
    today = timezone.now().date()
    main_treasury = Treasury.objects.get(code='MAIN')
    prod_treasury = Treasury.objects.get(code='PROD_TREASURY')
    workshop, _ = Workshop.objects.get_or_create(name="ورشة الإنتاج المجمعة", defaults={'workshop_type': 'internal'})
    
    # 1. CLEANUP PREVIOUS MOCKS
    ManufacturingOrder.objects.filter(start_date=today).delete()
    TreasuryTransaction.objects.filter(date=today, description__icontains="TAHYAAF TEST").delete()

    # 2. LOAD 200g RAW GOLD TO MAIN
    TreasuryTransaction.objects.create(
        treasury=main_treasury,
        transaction_type='gold_in',
        gold_weight=Decimal('200.00'),
        gold_carat=carat_18,
        description="TAHYAAF TEST: Loading 200g",
        created_by=admin_user,
        date=today
    )

    # 3. TRANSFER TO PROD
    TreasuryTransfer.objects.create(
        from_treasury=main_treasury,
        to_treasury=prod_treasury,
        gold_weight=Decimal('200.00'),
        gold_carat=carat_18,
        status='completed',
        initiated_by=admin_user,
        confirmed_by=admin_user,
        notes="TAHYAAF TEST: Transfer 200g Raw",
        date=today
    )

    # 4. SIMULATE PIECE WITH STONES (THE TAHYAAF CASE)
    # Scenario: Piece takes 15g Gold. It has 1.00 Carat stones.
    # Tahyaaf: 1.00 Carat = 0.2g Gold.
    # Gross Weight becomes 14.80g (Net Gold) + 0.2g (Stones) = 15.00g Gross? 
    # Let's say we returned 14.90g Gross.
    # Net Gold = 14.90 - 0.2 = 14.70.
    # Scrap = 15.00 - 14.70 = 0.30.

    print("\n--- Creating Order with Stones to verify Scrap calculation ---")
    order = ManufacturingOrder.objects.create(
        order_number=f"TAH-ORD-{timezone.now().strftime('%M%S')}",
        workshop=workshop,
        carat=carat_18,
        input_weight=Decimal('15.00'),
        output_weight=Decimal('14.90'), # Gross weight returned
        status='draft',
        start_date=today
    )
    
    # Manually set total_stone_weight to simulate the signal (or create OrderStone)
    # We'll create an OrderStone to trigger the signal
    print("Creating OrderStone (1.00 Carat)...")
    diamond, _ = Stone.objects.get_or_create(name="Diamond", defaults={'unit': 'قيراط'})
    from manufacturing.models import OrderStone
    OrderStone.objects.create(order=order, stone=diamond, quantity=Decimal('1.00'))
    
    # Refresh order to get updated total_stone_weight from signal
    order.refresh_from_db()
    print(f"Update Signal -> Total Stone Weight (Grams): {order.total_stone_weight}g")
    
    # Now simulate moving to completed to trigger scrap calc (done in pre_save)
    order.status = 'completed'
    order.save()
    
    print(f"Order Completed -> Scrap Weight: {order.scrap_weight}g")
    
    # EXPECTED: 
    # Net Gold = 14.90 - 0.2 = 14.70
    # Scrap = 15.00 - 14.70 = 0.30
    
    expected_scrap = Decimal('15.00') - (Decimal('14.90') - Decimal('0.20'))
    if abs(order.scrap_weight - expected_scrap) < 0.001:
        print("SUCCESS: Scrap calculation with Tahyaaf is CORRECT.")
    else:
        print(f"FAILED: Expected {expected_scrap}, got {order.scrap_weight}")

if __name__ == '__main__':
    test_tahyaaf_in_production()
