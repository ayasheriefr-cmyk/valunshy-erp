
import os
import sys
import django
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Stone, StoneCut, StoneCategoryGroup

def populate_stones():
    """إضافة أحجار تجريبية لقاعدة البيانات"""
    
    print("بدء إضافة الأحجار...")
    
    # 1. Create Category Groups if not exist
    group1, _ = StoneCategoryGroup.objects.get_or_create(
        code=1,
        defaults={
            'name': 'ألماس طبيعي',
            'short_code': 'DIA',
            'commission': 0.05
        }
    )
    
    group2, _ = StoneCategoryGroup.objects.get_or_create(
        code=2,
        defaults={
            'name': 'زركون',
            'short_code': 'ZIR',
            'commission': 0.03
        }
    )
    
    # 2. Create Stone Cuts
    cut1, _ = StoneCut.objects.get_or_create(
        code='RND',
        defaults={
            'name': 'دائري (Round)',
            'description': 'قطع دائري كلاسيكي',
            'category_group': group1
        }
    )
    
    cut2, _ = StoneCut.objects.get_or_create(
        code='PRN',
        defaults={
            'name': 'أميرة (Princess)',
            'description': 'قطع مربع',
            'category_group': group1
        }
    )
    
    cut3, _ = StoneCut.objects.get_or_create(
        code='EMR',
        defaults={
            'name': 'زمرد (Emerald)',
            'description': 'قطع مستطيل',
            'category_group': group1
        }
    )
    
    cut4, _ = StoneCut.objects.get_or_create(
        code='ZRC',
        defaults={
            'name': 'زركون عادي',
            'description': 'أحجار زركون للاستخدام العادي',
            'category_group': group2
        }
    )
    
    # 3. Create Sample Stones
    stones_data = [
        ('ألماس دائري 0.5 قيراط', 'Diamond', cut1, 'carat', 50),
        ('ألماس دائري 1 قيراط', 'Diamond', cut1, 'carat', 20),
        ('ألماس أميرة 0.3 قيراط', 'Diamond', cut2, 'carat', 80),
        ('ألماس زمرد 0.7 قيراط', 'Diamond', cut3, 'carat', 30),
        ('زركون أبيض 5 ملم', 'Zircon', cut4, 'cm', 200),
        ('زركون ملون 3 ملم', 'Zircon', cut4, 'cm', 150),
    ]
    
    for name, stone_type, stone_cut, unit, stock in stones_data:
        stone, created = Stone.objects.get_or_create(
            name=name,
            defaults={
                'stone_type': stone_type,
                'stone_cut': stone_cut,
                'unit': unit,
                'current_stock': stock
            }
        )
        if created:
            print(f"✓ تم إضافة: {name}")
        else:
            print(f"- موجود مسبقاً: {name}")
    
    print(f"\n✅ تم إضافة {Stone.objects.count()} حجر/فص بنجاح!")

if __name__ == "__main__":
    populate_stones()
