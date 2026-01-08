
import os
import django
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, Workshop, ProductionStage

print("Workshop Details:")
workshops = Workshop.objects.filter(id__in=[24, 26, 29])
for ws in workshops:
    print(f"ID: {ws.id}, Name: {ws.name}, Default Stage: {ws.default_stage_name}")

# Pick one order to move
order = ManufacturingOrder.objects.get(order_number='AUTO-16587655')
print(f"\nMoving Order {order.order_number} from {order.workshop.name} (ID: {order.workshop_id}) to Workshop ID 29...")

from django.db import transaction
from django.utils import timezone
from decimal import Decimal

target_ws = Workshop.objects.get(id=29)

with transaction.atomic():
    # Simulate the logic in views.py move_order
    output_weight = order.input_weight # Simplified
    powder_weight = Decimal('0')
    
    # Close current stage
    current_stage = order.stages.filter(end_datetime__isnull=True).last()
    if current_stage:
        print(f"Closing stage {current_stage.id} (Workshop: {current_stage.workshop.name})")
        current_stage.output_weight = output_weight
        current_stage.powder_weight = powder_weight
        current_stage.next_workshop = target_ws
        current_stage.save()
    
    # Create next stage
    new_stage = ProductionStage.objects.create(
        order=order,
        workshop=target_ws,
        stage_name=target_ws.default_stage_name or 'crafting',
        input_weight=output_weight,
        start_datetime=timezone.now()
    )
    print(f"Created new stage {new_stage.id} for {target_ws.name}")
    
    # Update Order
    order.workshop = target_ws
    order.save()

print(f"Move Complete. Order {order.order_number} workshop is now: {order.workshop.id} ({order.workshop.name})")

# Verify active orders grouping
active_statuses = ['in_progress', 'casting', 'crafting', 'polishing', 'qc_pending', 'tribolish', 'qc_failed']
active_orders = ManufacturingOrder.objects.filter(status__in=active_statuses)
orders_at_29 = active_orders.filter(workshop_id=29)
print(f"Orders at Workshop 29 now: {[o.order_number for o in orders_at_29]}")
