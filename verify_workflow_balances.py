import os
import django
from decimal import Decimal
from django.db.models import Sum, Q

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop, ManufacturingOrder, Stone, OrderStone, ProductionStage
from finance.treasury_models import Treasury, TreasuryTransaction

def verify_balances():
    print("=== Magic Workflow Balance Audit ===")
    
    # 1. Workshop Balances
    print("\n[1] Workshop Balances (Current Debt/Stock)")
    print("-" * 80)
    print(f"{'Workshop Name':<25} | {'G18':<8} | {'G21':<8} | {'G24':<8} | {'Scrap':<8} | {'Powder':<8}")
    print("-" * 80)
    
    import sys
    # For Windows console, try to set encoding if not interactive, or just use try/except
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    workshops = Workshop.objects.all()
    for ws in workshops:
        try:
            print(f"{ws.name[:25]:<25} | {ws.gold_balance_18:<8.2f} | {ws.gold_balance_21:<8.2f} | {ws.gold_balance_24:<8.2f} | {ws.scrap_balance_18:<8.2f} | {ws.filings_balance_18:<8.2f}")
        except UnicodeEncodeError:
            # Fallback to ID if name cannot be encoded
            print(f"WS ID {ws.id:<20} | {ws.gold_balance_18:<8.2f} | {ws.gold_balance_21:<8.2f} | {ws.gold_balance_24:<8.2f} | {ws.scrap_balance_18:<8.2f} | {ws.filings_balance_18:<8.2f}")

    # 2. Active Orders (Gold in Flight)
    print("\n[2] Active Orders (Gold in Flight)")
    print("-" * 80)
    active_orders = ManufacturingOrder.objects.filter(
        status__in=['in_progress', 'casting', 'crafting', 'polishing', 'qc_pending', 'tribolish', 'qc_failed']
    ).select_related('workshop', 'carat')
    
    total_active_weight = 0
    print(f"{'Order #':<15} | {'Workshop':<20} | {'Carat':<8} | {'Weight':<10}")
    print("-" * 80)
    for order in active_orders:
        ws_name = order.workshop.name if order.workshop else "Unassigned"
        print(f"{order.order_number:<15} | {ws_name[:20]:<20} | {order.carat.name:<8} | {order.input_weight:<10.3f}")
        total_active_weight += order.input_weight
    print("-" * 80)
    print(f"Total Gold in Flight: {total_active_weight:.3f} g")

    # 3. Stone Inventory Audit
    print("\n[3] Stone Inventory Audit")
    print("-" * 80)
    stones = Stone.objects.all()
    print(f"{'Stone Name':<30} | {'Stock':<10} | {'Unit':<10} | {'In Orders':<10}")
    print("-" * 80)
    for stone in stones:
        in_orders = OrderStone.objects.filter(stone=stone, order__status__in=['in_progress', 'casting', 'crafting', 'polishing', 'qc_pending', 'tribolish', 'qc_failed']).aggregate(total=Sum('quantity_issued'))['total'] or 0
        print(f"{stone.name[:30]:<30} | {stone.current_stock:<10.3f} | {stone.unit:<10} | {in_orders:<10.3f}")

    # 4. Global Gold Reconcilliation (Treasury vs Production)
    print("\n[4] Global Gold Reconciliation")
    print("-" * 80)
    
    # Total Gold issued for production (from Production & WIP treasuries)
    prod_related_tx = TreasuryTransaction.objects.filter(
        Q(description__icontains="تشغيل") | Q(description__icontains="تصنيع") | Q(reference_type="manufacturing_order"),
        transaction_type="gold_out"
    ).aggregate(total=Sum('gold_weight'))['total'] or 0
    
    # Total Gold returned as finished products
    finished_tx = TreasuryTransaction.objects.filter(
        transaction_type="finished_goods_in"
    ).aggregate(total=Sum('gold_weight'))['total'] or 0
    
    # Total Gold currently in workshops (Summary of all gold_balance fields)
    workshop_gold = sum([
        workshops.aggregate(Sum('gold_balance_18'))['gold_balance_18__sum'] or 0,
        workshops.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0,
        workshops.aggregate(Sum('gold_balance_24'))['gold_balance_24__sum'] or 0
    ])

    print(f"Total Issued from Treasuries: {prod_related_tx:.3f} g")
    print(f"Total Returned (Finished):    {finished_tx:.3f} g")
    print(f"Current Workshop Gold Debt:   {workshop_gold:.3f} g")
    print(f"Expected in Workshops:        {prod_related_tx - finished_tx:.3f} g (approx)")
    
    diff = workshop_gold - (prod_related_tx - finished_tx)
    print(f"Discrepancy:                  {diff:.3f} g")
    if abs(diff) < 0.01:
        print("RESULT: ACCOUNT IS BALANCED ✅")
    else:
        print("RESULT: DISCREPANCY DETECTED ⚠️")

if __name__ == "__main__":
    verify_balances()
