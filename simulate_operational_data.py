import os
import django
import datetime
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder, Stone, OrderStone, ProductionStage, Workshop, RawMaterial
from core.models import Carat, Branch
from inventory.models import Item, Category

def simulate_operational_data():
    # 1. Setup basics
    carat_18 = Carat.objects.filter(name__contains='18').first()
    carat_21 = Carat.objects.filter(name__contains='21').first()
    main_branch = Branch.objects.first()
    category = Category.objects.get_or_create(name="أطقم الماس")[0]
    
    stones = list(Stone.objects.all())
    workshops = list(Workshop.objects.all())
    raw_materials = list(RawMaterial.objects.all())
    
    if not stones or not workshops or not raw_materials:
        print("Missing basic data (stones, workshops, or raw materials). Please ensure they exist.")
        return

    # 2. Daily simulation for December 2025
    start_date = datetime.date(2025, 12, 1)
    end_date = datetime.date(2025, 12, 30)
    current_date = start_date

    while current_date <= end_date:
        # Create 2-4 orders per day
        for i in range(random.randint(2, 4)):
            workshop = random.choice(workshops)
            carat = random.choice([carat_18, carat_21])
            input_weight = Decimal(random.uniform(50, 150)).quantize(Decimal('0.001'))
            
            # Use timestamp + random to ensure uniqueness
            order_num = f"ORD-{current_date.month}-{current_date.year}-{random.randint(100000, 999999)}"
            
            # Create Order
            order = ManufacturingOrder.objects.create(
                order_number=order_num,
                workshop=workshop,
                carat=carat,
                input_weight=input_weight,
                status='completed',
                start_date=current_date,
                end_date=current_date,
                item_name_pattern=f"طقم ذهب {carat.name}",
                target_branch=main_branch
            )
            
            # Attach Stones
            num_stones = random.randint(1, 3)
            selected_stones = random.sample(stones, min(num_stones, len(stones)))
            total_stone_w = Decimal('0')
            for s in selected_stones:
                qty = Decimal(random.uniform(1, 10)).quantize(Decimal('0.001'))
                OrderStone.objects.create(order=order, stone=s, quantity=qty)
                total_stone_w += qty * Decimal('0.2') # Carat to Gram (approximation)
                
            order.total_stone_weight = total_stone_w
            order.output_weight = input_weight - Decimal(random.uniform(0.5, 2.0)) # Scrap
            order.scrap_weight = input_weight - order.output_weight
            order.save()
            
            # Create Stages
            curr_time = datetime.datetime.combine(current_date, datetime.time(9, 0))
            for stage_code, stage_label in ProductionStage.STAGE_CHOICES:
                duration_mins = random.randint(30, 180)
                end_time = curr_time + datetime.timedelta(minutes=duration_mins)
                
                ProductionStage.objects.create(
                    order=order,
                    stage_name=stage_code,
                    input_weight=input_weight,
                    output_weight=input_weight, # Simplified
                    technician="فني محاكاة",
                    start_datetime=curr_time,
                    end_datetime=end_time
                )
                curr_time = end_time + datetime.timedelta(minutes=15) # Buffer

        current_date += datetime.timedelta(days=1)

    print(f"Simulation completed for {start_date} to {end_date}")

if __name__ == "__main__":
    simulate_operational_data()
