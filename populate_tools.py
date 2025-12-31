"""
سكريبت لإضافة أدوات التصنيع الافتراضية
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import InstallationTool
from core.models import Carat

def create_default_tools():
    # Get carats
    carat_18 = Carat.objects.filter(name__contains='18').first()
    carat_21 = Carat.objects.filter(name__contains='21').first()
    
    tools = [
        # Gold-based tools (weight)
        {'name': 'سلك ليزر ذهب 18', 'tool_type': 'gold_wire', 'unit': 'gram', 'weight': 0, 'min_weight': 5, 'carat': carat_18, 'description': 'سلك ذهب للحام بالليزر عيار 18'},
        {'name': 'سلك ليزر ذهب 21', 'tool_type': 'gold_wire', 'unit': 'gram', 'weight': 0, 'min_weight': 5, 'carat': carat_21, 'description': 'سلك ذهب للحام بالليزر عيار 21'},
        {'name': 'لحام ذهب 18', 'tool_type': 'gold_solder', 'unit': 'gram', 'weight': 0, 'min_weight': 10, 'carat': carat_18, 'description': 'لحام ذهب للصياغة عيار 18'},
        {'name': 'لحام ذهب 21', 'tool_type': 'gold_solder', 'unit': 'gram', 'weight': 0, 'min_weight': 10, 'carat': carat_21, 'description': 'لحام ذهب للصياغة عيار 21'},
        {'name': 'كيديم', 'tool_type': 'cadmium', 'unit': 'gram', 'weight': 0, 'min_weight': 5, 'carat': None, 'description': 'كيديم للحام'},
        {'name': 'رقائق ذهب 18', 'tool_type': 'gold_sheet', 'unit': 'gram', 'weight': 0, 'min_weight': 20, 'carat': carat_18, 'description': 'رقائق ذهب للتشكيل'},
        
        # Regular consumables
        {'name': 'شمع صب', 'tool_type': 'consumable', 'unit': 'piece', 'quantity': 0, 'min_quantity': 10, 'description': 'شمع للصب والقوالب'},
        {'name': 'جبس صب', 'tool_type': 'consumable', 'unit': 'piece', 'quantity': 0, 'min_quantity': 5, 'description': 'جبس للقوالب'},
        {'name': 'بوراكس', 'tool_type': 'consumable', 'unit': 'piece', 'quantity': 0, 'min_quantity': 3, 'description': 'مادة تنظيف للصهر'},
        {'name': 'حمض الكبريتيك', 'tool_type': 'consumable', 'unit': 'piece', 'quantity': 0, 'min_quantity': 2, 'description': 'للتنظيف والتلميع'},
        
        # Equipment
        {'name': 'مبرد ناعم', 'tool_type': 'equipment', 'unit': 'piece', 'quantity': 0, 'min_quantity': 5, 'description': 'مبرد للتشطيب الناعم'},
        {'name': 'مبرد خشن', 'tool_type': 'equipment', 'unit': 'piece', 'quantity': 0, 'min_quantity': 5, 'description': 'مبرد للتشكيل الخشن'},
        {'name': 'زرادية صغيرة', 'tool_type': 'equipment', 'unit': 'piece', 'quantity': 0, 'min_quantity': 3, 'description': 'زرادية للأعمال الدقيقة'},
        {'name': 'ملقط تركيب فصوص', 'tool_type': 'equipment', 'unit': 'piece', 'quantity': 0, 'min_quantity': 3, 'description': 'ملقط لتركيب الأحجار'},
        {'name': 'قلم نقش', 'tool_type': 'equipment', 'unit': 'piece', 'quantity': 0, 'min_quantity': 2, 'description': 'قلم للنقش والزخرفة'},
        
        # Spare parts
        {'name': 'رأس بوري', 'tool_type': 'spare_part', 'unit': 'piece', 'quantity': 0, 'min_quantity': 2, 'description': 'رأس بوري للحام'},
        {'name': 'فرشة تلميع', 'tool_type': 'spare_part', 'unit': 'piece', 'quantity': 0, 'min_quantity': 5, 'description': 'فرشة للتلميع'},
    ]
    
    created_count = 0
    for tool_data in tools:
        name = tool_data.pop('name')
        obj, created = InstallationTool.objects.get_or_create(name=name, defaults=tool_data)
        if created:
            created_count += 1
            print(f"[OK] Added: {name}")
        else:
            print(f"[-] Exists: {name}")
    
    print(f"\n=== Added {created_count} new tools ===")

if __name__ == '__main__':
    create_default_tools()
