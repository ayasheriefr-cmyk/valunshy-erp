import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import StoneCategoryGroup, StoneCut, StoneModel, StoneSize, Stone

def populate_diamond_data():
    print("Starting diamond data population...")

    # 1. Create or get Category Group
    diamond_group, _ = StoneCategoryGroup.objects.get_or_create(
        code=100,
        defaults={'name': 'أحجار ألماس أساسية', 'short_code': 'DIA', 'commission': Decimal('0.00')}
    )

    # 2. Define Shapes and their common sizes
    # Data source summarized from Brilliance.com
    # Format: { 'name': 'Arabic Name', 'code': 'Code', 'sizes': [ (carat, mm), ... ] }
    shapes_data = {
        'Round': {
            'arabic': 'دائري (Round)',
            'code': 'RD',
            'sizes': [
                (0.01, 1.3), (0.02, 1.7), (0.03, 2.0), (0.04, 2.2), (0.05, 2.4),
                (0.10, 3.0), (0.15, 3.4), (0.20, 3.8), (0.25, 4.0), (0.50, 5.0),
                (0.75, 5.75), (1.00, 6.5), (1.50, 7.3), (2.00, 8.0), (3.00, 9.1)
            ]
        },
        'Princess': {
            'arabic': 'برنسيس (Princess)',
            'code': 'PR',
            'sizes': [
                (0.25, 3.25), (0.50, 4.9), (0.75, 5.25), (1.00, 5.5), 
                (1.50, 6.5), (2.00, 7.0), (3.00, 8.0)
            ]
        },
        'Cushion': {
            'arabic': 'كوشن (Cushion)',
            'code': 'CU',
            'sizes': [
                (0.25, 3.25), (0.50, 4.5), (0.75, 5.0), (1.00, 5.5),
                (1.50, 6.0), (2.00, 6.5), (3.00, 7.5)
            ]
        },
        'Emerald': {
            'arabic': 'زمردي (Emerald)',
            'code': 'EM',
            'sizes': [
                (0.50, 5.0), (0.75, 6.0), (1.00, 7.0), (1.50, 8.0), (2.00, 8.5)
            ]
        },
        'Oval': {
            'arabic': 'بيضاوي (Oval)',
            'code': 'OV',
            'sizes': [
                (0.50, 6.0), (0.75, 7.0), (1.00, 7.5), (1.50, 8.5), (2.00, 9.0)
            ]
        },
        'Pear': {
            'arabic': 'كمثرى (Pear)',
            'code': 'PS',
            'sizes': [
                (0.50, 7.0), (0.75, 8.0), (1.00, 8.5), (1.50, 9.5), (2.00, 10.5)
            ]
        },
        'Marquise': {
            'arabic': 'ماركيز (Marquise)',
            'code': 'MQ',
            'sizes': [
                (0.50, 8.0), (0.75, 9.0), (1.00, 10.0), (1.50, 11.5), (2.00, 12.5)
            ]
        }
    }

    # Tracking for unique codes - find the max existing code and start from there
    from django.db.models import Max
    max_code = StoneSize.objects.aggregate(Max('code'))['code__max'] or 999
    size_code_counter = max_code + 1

    for shape_name, data in shapes_data.items():
        # Create StoneCut
        cut, _ = StoneCut.objects.get_or_create(
            code=data['code'],
            defaults={
                'name': data['arabic'],
                'category_group': diamond_group
            }
        )

        # Create a default StoneModel for this cut if it doesn't exist
        model, _ = StoneModel.objects.get_or_create(
            code=f"STD-{data['code']}",
            defaults={
                'name': f"مقاسات {data['arabic']} قياسية",
                'stone_cut': cut
            }
        )

        for carat, mm in data['sizes']:
            # Create StoneSize
            # For simplicity, weight_from and weight_to are centered around the target carat
            w_from = Decimal(str(carat)) * Decimal('0.95')
            w_to = Decimal(str(carat)) * Decimal('1.05')
            
            # Special case for small Round (close to Nawaem 10 range)
            if shape_name == 'Round' and carat == 0.10:
                # This could be the base for M10
                pass

            StoneSize.objects.get_or_create(
                stone_cut=cut,
                stone_model=model,
                weight_from=w_from,
                weight_to=w_to,
                size_mm=Decimal(str(mm)),
                defaults={
                    'code': size_code_counter,
                    'stone_type': 'Diamond',
                    'short_code': f"{data['code']}-{carat}",
                }
            )
            size_code_counter += 1

    # 3. Special Handling for Nawaem 10 (M10)
    print("Setting up Nawaem 10 (M10)...")
    m10_cut, _ = StoneCut.objects.get_or_create(
        code='M10',
        defaults={'name': 'نواعم 10 (M10)', 'category_group': diamond_group}
    )
    
    m10_model, _ = StoneModel.objects.get_or_create(
        code='M10-STD',
        defaults={'name': 'نواعم 10 أساسي', 'stone_cut': m10_cut}
    )

    m10_size = StoneSize.objects.filter(code=8).first()
    if not m10_size:
        m10_size = StoneSize.objects.create(
            code=8,
            stone_cut=m10_cut,
            stone_model=m10_model,
            stone_type='M10',
            weight_from=Decimal('0.075'),
            weight_to=Decimal('0.120'),
            size_mm=Decimal('3.0'),
            price_per_carat=Decimal('950.00')
        )
    else:
        m10_size.stone_cut = m10_cut
        m10_size.stone_model = m10_model
        m10_size.weight_from = Decimal('0.075')
        m10_size.weight_to = Decimal('0.120')
        m10_size.save()
    
    print("Linking existing M10 stones...")
    stones = Stone.objects.filter(name__icontains='M10') | Stone.objects.filter(stone_type__icontains='m0.10')
    for s in stones:
        s.stone_size = m10_size
        s.stone_cut = m10_cut
        s.save()

    print("Success! Diamond data populated.")

if __name__ == "__main__":
    populate_diamond_data()
