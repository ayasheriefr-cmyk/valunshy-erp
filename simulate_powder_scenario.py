
import os
import sys
import django
from decimal import Decimal
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop, ManufacturingOrder, WorkshopSettlement
from core.models import Carat

def run_simulation():
    print("\n--- بدء محاكاة دورة التصنيع والبودر ---\n")

    # 1. Setup Data
    carat_18, _ = Carat.objects.get_or_create(name='18K', defaults={'code': '18', 'purity': 0.750})
    
    # Create or Get Workshop
    workshop, _ = Workshop.objects.get_or_create(
        name="ورشة المعلم إبراهيم (تجربة)",
        defaults={'workshop_type': 'external'}
    )
    
    # Reset Balances for Clarity
    workshop.gold_balance_18 = Decimal('0.000')
    workshop.save()
    
    print(f"1. رصيد الورشة قبل البدء: {workshop.gold_balance_18} جرام")

    print(f"1. رصيد الورشة قبل البدء: {workshop.gold_balance_18} جرام")

    # Cleanup Previous Data
    ManufacturingOrder.objects.filter(order_number="ORD-SIM-001").delete()
    WorkshopSettlement.objects.filter(workshop=workshop).delete()

    # 2. Create Order (Issue Gold) -> Should Increase Balance
    print("\n[تحرك 1] إنشاء أمر تصنيع وصرف 100 جرام ذهب")
    order = ManufacturingOrder.objects.create(
        order_number="ORD-SIM-001",
        workshop=workshop,
        carat=carat_18,
        input_weight=Decimal('100.000'),
        status='draft' # Start as draft
    )
    
    # Move to In Progress (Trigger Issuance)
    order.status = 'in_progress'
    order.save()
    
    workshop.refresh_from_db()
    print(f"-> تم صرف الذهب. رصيد الورشة (مديونية): {workshop.gold_balance_18} جرام")
    
    # 3. Complete Order (Receive Product) -> Should Decrease Balance
    print("\n[تحرك 2] إقفال الأمر واستلام منتج وزن 98 جرام")
    # Loss = 100 (In) - 98 (Out) = 2 Grams (Physical Loss + Powder)
    
    order.output_weight = Decimal('98.000')
    order.status = 'completed'
    order.save()
    
    workshop.refresh_from_db()
    print(f"-> تم استلام المنتج. رصيد الورشة الحالي: {workshop.gold_balance_18} جرام")
    print(f"   (ملاحظة: الرصيد 2 جرام ده عبارة عن الهالك والبودر اللي لسه في عهدة الورشة)")

    # 4. End of Day: Receive Powder Settlement
    print("\n[تحرك 3] آخر اليوم: عمل تسوية استلام بودر (1.5 جرام)")
    
    settlement = WorkshopSettlement.objects.create(
        workshop=workshop,
        settlement_type='powder_receive',
        weight=Decimal('1.500'),
        carat=carat_18,
        notes="استلام بودر تجميعة اليوم"
    )
    
    workshop.refresh_from_db()
    print(f"-> تم حفظ التسوية.")
    print(f"-> رصيد الورشة النهائي: {workshop.gold_balance_18} جرام")
    print(f"   (المتبقي 0.5 جرام ده الهالك الحتمي الغير مسترد)")

    print("\n--- انتهت المحاكاة بنجاح ---")

if __name__ == "__main__":
    run_simulation()
