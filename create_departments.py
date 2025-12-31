import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury
from manufacturing.models import Workshop

def create_departments():
    # 1. Ensure Main Treasury exists
    main_treasury, created = Treasury.objects.get_or_create(
        code='1',
        defaults={'name': 'الخزينة الرئيسية', 'treasury_type': 'main'}
    )
    if created:
        print(f"Created Main Treasury: {main_treasury.code}")
    else:
        print(f"Found existing Main Treasury: {main_treasury.code}")

    # List of departments from image
    departments = [
        ('1', 'تحت التشغيل'),
        ('2', 'ذهب كسر'),
        ('3', 'تزجه قاسم'),
        ('4', 'تزجه بابلو'),
        ('5', 'جلاه انور تحت التشغيل'),
        ('6', 'تركيب مونموى'),
        ('7', 'تركيب سونيل'),
        ('8', 'تركيب اربان'),
        ('9', 'تركيب فيم'),
        ('10', 'برادة تزجة قاسم'),
    ]

    for dep_code, dep_name in departments:
        # Check if a workshop with similar name exists to link it
        workshop = Workshop.objects.filter(name__icontains=dep_name.split()[0]).first()
        
        sub_t, t_created = Treasury.objects.get_or_create(
            code=f"DEP-{dep_code}",
            defaults={
                'name': dep_name,
                'parent': main_treasury,
                'treasury_type': 'production' if 'تركيب' in dep_name or 'تزجه' in dep_name or 'تحت التشغيل' in dep_name else 'gold_raw',
                'workshop': workshop
            }
        )
        if t_created:
            print(f"Created sub-treasury Code: DEP-{dep_code}")
        else:
            # Update parent if already exists but not linked
            if sub_t.parent != main_treasury:
                sub_t.parent = main_treasury
                sub_t.save()
                print(f"Updated parent for Code: DEP-{dep_code}")
            print(f"Sub-treasury already exists Code: DEP-{dep_code}")

if __name__ == "__main__":
    create_departments()
