
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, Workshop
from collections import defaultdict

import sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. Fetch Workshops
workshops = Workshop.objects.all()
print(f"Workshops Count: {workshops.count()}")
for w in workshops:
    print(f"Workshop: {w.id} - {w.name}")

# 2. Fetch Active Orders
statuses = ['in_progress', 'casting', 'crafting', 'polishing', 'qc_pending', 'tribolish', 'qc_failed']
active_orders = ManufacturingOrder.objects.filter(
    status__in=statuses
).select_related('workshop')

print(f"\nActive Orders Query Count: {active_orders.count()}")

# 3. Simulate Grouping
orders_by_workshop = defaultdict(list)
for order in active_orders:
    print(f"Order {order.order_number}: Status={order.status}, WorkshopID={order.workshop_id}")
    if order.workshop_id:
        orders_by_workshop[order.workshop_id].append(order)
    else:
        print(f"  !! WARNING: Order {order.order_number} has NO workshop!")

# 4. Check Mapping
print("\nWorkflow Data Simulation:")
for ws in workshops:
    ws_orders = orders_by_workshop.get(ws.id, [])
    print(f"Workshop {ws.name} ({ws.id}) has {len(ws_orders)} orders.")
