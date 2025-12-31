import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop, ManufacturingOrder, WorkshopSettlement
from django.db.models import Sum

def debug_balances():
    print("--- Workshop Balances ---")
    workshops = Workshop.objects.all()
    for w in workshops:
        print(f"ID: {w.id:2} | Name: {w.name:15} | 18k: {w.gold_balance_18:10.3f} | 21k: {w.gold_balance_21:10.3f} | Labor: {w.labor_balance:10.2f}")

    print("\n--- Summary Totals ---")
    total_18 = workshops.aggregate(Sum('gold_balance_18'))['gold_balance_18__sum'] or 0
    total_21 = workshops.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0
    total_labor = workshops.aggregate(Sum('labor_balance'))['labor_balance__sum'] or 0
    print(f"Total 18k: {total_18:10.3f}")
    print(f"Total 21k: {total_21:10.3f}")
    print(f"Total Labor: {total_labor:10.2f}")

    print("\n--- Orders with Costs ---")
    orders = ManufacturingOrder.objects.exclude(manufacturing_pay=0)
    print(f"Orders with Pay > 0: {orders.count()}")
    for o in orders:
        print(f"Order: {o.order_number} | Workshop: {o.workshop.name} | Pay: {o.manufacturing_pay}")

    active_orders = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled'])
    active_weight = active_orders.aggregate(Sum('input_weight'))['input_weight__sum'] or 0
    print(f"\nActive Weight (under processing): {active_weight:10.3f}")

if __name__ == "__main__":
    debug_balances()
