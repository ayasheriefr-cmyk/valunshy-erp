import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import StoneCut, StoneSize, Stone

def populate_stones_from_sizes():
    print("Creating Stone inventory records for all Sizes...")
    
    sizes = StoneSize.objects.all()
    created_count = 0
    
    for size in sizes:
        # Create a descriptive name
        name = f"مقاس {size.weight_from}-{size.weight_to} ct"
        if size.stone_type == 'M10':
            name = "M10"
            
        stone = Stone.objects.filter(stone_cut=size.stone_cut, stone_size=size).first()
        if not stone:
            stone = Stone.objects.create(
                stone_cut=size.stone_cut,
                stone_size=size,
                name=name,
                stone_type=size.stone_type or 'Diamond',
                unit='carat'
            )
            created_count += 1
            
    print(f"Success! Created {created_count} new selectable stones in inventory.")

if __name__ == "__main__":
    populate_stones_from_sizes()
