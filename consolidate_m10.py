اناimport os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Stone, StoneSize, StoneModel

def consolidate_m10():
    print("Starting M10 consolidation...")
    
    # 1. Find the M10 model
    m10_model = StoneModel.objects.filter(name__icontains='M10').first()
    if not m10_model:
        print("Error: M10 model not found.")
        return

    # 2. Update or create the StoneSize group for M10
    # The user referred to "m10" which matches Model name "M10" (id 8 in previous check)
    # Range: 0.075 to 0.12
    size, created = StoneSize.objects.get_or_create(
        code=1, 
        defaults={
            'stone_cut': m10_model.stone_cut,
            'stone_model': m10_model,
            'weight_from': Decimal('0.075'),
            'weight_to': Decimal('0.120'),
            'price_per_carat': Decimal('950.00'), # Keep existing or default
            'size_mm': Decimal('0.00')
        }
    )
    
    if not created:
        size.weight_from = Decimal('0.075')
        size.weight_to = Decimal('0.120')
        size.save()
    
    print(f"Set StoneSize {size.code} (M10) range to: {size.weight_from} - {size.weight_to}")

    # 3. Identify and link Stones
    # We look for stones that are either named M10/m10 or currently have that specific model/size
    stones = Stone.objects.filter(
        name__icontains='M10'
    ) | Stone.objects.filter(
        stone_type__icontains='m0.10'
    )
    
    updated_count = 0
    for stone in stones:
        stone.stone_size = size
        stone.save()
        updated_count += 1
        print(f"Linked Stone: {stone.name} to M10 size group.")

    print(f"Successfully consolidated {updated_count} stones under M10 group.")

if __name__ == "__main__":
    consolidate_m10()
