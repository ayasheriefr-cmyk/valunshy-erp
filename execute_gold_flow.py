import os
import django
import sys
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from finance.treasury_models import Treasury, TreasuryTransaction, TreasuryTransfer
from manufacturing.models import Workshop, ManufacturingOrder, WorkshopTransfer
from core.models import Carat
from django.contrib.auth.models import User
from django.db import transaction

def execute_flow():
    today = timezone.now().date()
    admin_user = User.objects.filter(is_superuser=True).first()
    carat_18 = Carat.objects.filter(name__contains='18').first()
    
    if not carat_18:
        print("خطأ: لم يتم العثور على عيار 18")
        return

    # IDs specific to this system
    MAIN_ID = 1
    PROD_ID = 7
    QASSEM_WS_ID = 6
    LASER_WS_ID = 12
    
    ts = int(timezone.now().timestamp())
    amount = Decimal('120.000')

    print(f"--- بدء دورة حياة الذهب (120 جرام عيار 18) بتوقيت {timezone.now()} ---")

    try:
        with transaction.atomic():
            # 1. الاستلام في الخزينة الرئيسية
            main_t = Treasury.objects.get(id=MAIN_ID)
            TreasuryTransaction.objects.create(
                treasury=main_t,
                transaction_type='gold_in',
                gold_weight=amount,
                gold_carat=carat_18,
                description=f"استلام مبدئي 120 جرام عيار 18 - {ts}",
                date=today,
                created_by=admin_user
            )
            print(f"تم تنفيذ المرحلة 1: استلام {amount} جرام في {main_t.name}")

            # 2. تحويل من الرئيسية إلى الإنتاج
            prod_t = Treasury.objects.get(id=PROD_ID)
            trf_1 = TreasuryTransfer.objects.create(
                from_treasury=main_t,
                to_treasury=prod_t,
                gold_weight=amount,
                gold_carat=carat_18,
                notes="تحويل عهدة من الرئيسية للإنتاج",
                date=today,
                initiated_by=admin_user,
                confirmed_by=admin_user,
                status='completed'
            )
            print(f"تم تنفيذ المرحلة 2: تحويل {amount} جرام من {main_t.name} إلى {prod_t.name}")

            # 3. فتح أمر شغل في قسم تزجه قاسم
            ws_qassem = Workshop.objects.get(id=QASSEM_WS_ID)
            order = ManufacturingOrder.objects.create(
                order_number=f"FLOW-{ts}",
                workshop=ws_qassem,
                carat=carat_18,
                input_weight=amount,
                status='in_progress',
                start_date=today
            )
            # نخصم من خزينة الإنتاج لنضعها في رصيد الورشة (يدوياً أو عبر إشارة)
            # لنقوم بعملية صرف عهدة للورشة
            TreasuryTransaction.objects.create(
                treasury=prod_t,
                transaction_type='gold_out',
                gold_weight=amount,
                gold_carat=carat_18,
                description=f"صرف أمر شغل {order.order_number} لورشة {ws_qassem.name}",
                date=today,
                created_by=admin_user
            )
            print(f"تم تنفيذ المرحلة 3: فتح أمر شغل {order.order_number} في {ws_qassem.name}")

            # 4. تحويل من قاسم إلى الليزر
            ws_laser = Workshop.objects.get(id=LASER_WS_ID)
            wtrf_1 = WorkshopTransfer.objects.create(
                transfer_number=f"WT-{ts}-1",
                from_workshop=ws_qassem,
                to_workshop=ws_laser,
                carat=carat_18,
                weight=amount,
                status='completed',
                date=today,
                initiated_by=admin_user
            )
            print(f"تم تنفيذ المرحلة 4: تحويل {amount} جرام من {ws_qassem.name} إلى {ws_laser.name}")

            # 5. تحويل من الليزر إلى قاسم
            wtrf_2 = WorkshopTransfer.objects.create(
                transfer_number=f"WT-{ts}-2",
                from_workshop=ws_laser,
                to_workshop=ws_qassem,
                carat=carat_18,
                weight=amount,
                status='completed',
                date=today,
                initiated_by=admin_user
            )
            print(f"تم تنفيذ المرحلة 5: إعادة {amount} جرام من {ws_laser.name} إلى {ws_qassem.name}")

            # 6. تسليم من قاسم لخزينة الإنتاج
            # سنقوم بتسجيل خسية مرتفعة (5 جرام من أصل 120 - حوالي 4.1%)
            scrap_weight = Decimal('5.000')
            output_weight = amount - scrap_weight
            
            order.status = 'completed'
            order.scrap_weight = scrap_weight
            order.output_weight = output_weight
            order.save()
            
            # استلام الذهب الصافي (المنتج) في الخزينة
            TreasuryTransaction.objects.create(
                treasury=prod_t,
                transaction_type='gold_in',
                gold_weight=output_weight,
                gold_carat=carat_18,
                description=f"استلام إنتاج تام (بذمة الخسية) أمر {order.order_number} من {ws_qassem.name}",
                date=today,
                created_by=admin_user
            )
            print(f"تم تنفيذ المرحلة 6: تسليم الإنتاج التام ({output_weight} جرام) مع تسجيل خسية ({scrap_weight} جرام) إلى {prod_t.name}")

            # 7. تسليم من الإنتاج للخزينة الرئيسية
            trf_2 = TreasuryTransfer.objects.create(
                from_treasury=prod_t,
                to_treasury=main_t,
                gold_weight=output_weight,
                gold_carat=carat_18,
                notes="تسليم الإنتاج التام (بعد الخسية) للخزينة الرئيسية",
                date=today,
                initiated_by=admin_user,
                confirmed_by=admin_user,
                status='completed'
            )
            print(f"تم تنفيذ المرحلة 7: تحويل المنتج النهائي ({output_weight} جرام) من {prod_t.name} إلى {main_t.name}")

        print("\n--- تمت العملية بنجاح كامل ---")

    except Exception as e:
        print(f"فشل في تنفيذ الدورة: {e}")

if __name__ == "__main__":
    execute_flow()
