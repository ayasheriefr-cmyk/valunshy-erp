
import os
import django
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, Workshop
from collections import defaultdict

# 1. Fetch exactly as views.py does
active_statuses = ['in_progress', 'casting', 'crafting', 'polishing', 'qc_pending', 'tribolish', 'qc_failed']
active_orders = ManufacturingOrder.objects.filter(
    status__in=active_statuses
).select_related('workshop', 'carat').prefetch_related('stages')

print(f"Total Active Orders: {active_orders.count()}")

orders_by_workshop = defaultdict(list)
for order in active_orders:
    print(f"Order: {order.order_number}, Workshop ID: {order.workshop_id}, Status: {order.status}")
    if order.workshop_id:
        orders_by_workshop[order.workshop_id].append(order)

# 2. Compare with Workshop list
workshops = Workshop.objects.filter(is_active=True)
print(f"\nActive Workshops in DB: {workshops.count()}")

for ws in workshops:
    ws_orders = orders_by_workshop.get(ws.id, [])
    print(f"Workshop: {ws.name} (ID: {ws.id}) -> Grouped Orders: {len(ws_orders)}")

# 3. Check for "Leaking" orders (Active but not in any active workshop)
active_ws_ids = set(workshops.values_list('id', flat=True))
for order in active_orders:
    if order.workshop_id and order.workshop_id not in active_ws_ids:
        ws = Workshop.objects.get(id=order.workshop_id)
        print(f"WARNING: Order {order.order_number} is in INACTIVE Workshop: {ws.name} (ID: {ws.id})")
