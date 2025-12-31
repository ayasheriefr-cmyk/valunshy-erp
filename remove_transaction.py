
import os
import django
from django.db import transaction
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


from finance.treasury_models import Treasury, TreasuryTransaction, TreasuryTransfer
from manufacturing.models import ManufacturingOrder, Workshop, WorkshopTransfer, WorkshopSettlement

def run():
    today = timezone.now().date()
    print(f"--- تنظيف شامل للنظام ({today}) ---")
    print("-" * 50)

    try:
        main_treasury = Treasury.objects.get(id=1)
    except Treasury.DoesNotExist:
        return

    with transaction.atomic():
        # --- 1. TREASURY CLEANUP ---
        # A. Delete 395.8 Transaction
        target_txs = TreasuryTransaction.objects.filter(
            treasury=main_treasury,
            date=today,
            gold_weight__gte=395.0, 
            gold_weight__lte=396.0
        )
        count = target_txs.count()
        if count > 0:
            for tx in target_txs:
                print(f"❌ حذف حركة خزينة: {tx.transaction_type} - {tx.gold_weight}g")
                if tx.reference_type == 'treasury_transfer' and tx.reference_id:
                    TreasuryTransfer.objects.filter(id=tx.reference_id).delete()
                tx.delete()
        
        # B. Force Treasury Balance
        main_treasury.gold_balance_18 = 5.11
        main_treasury.stones_balance = 0.2
        main_treasury.gold_balance_21 = 0
        main_treasury.gold_balance_24 = 0
        main_treasury.cash_balance = 0
        main_treasury.save()
        print(f"✅ تم ضبط الخزينة: 5.11 جم (18) | 0.2 قيراط")

        # --- 2. WORKSHOP RESET ---
        print("\n⏳ جاري تصفير الورش وإعادة الاحتساب من اليوم فقط...")
        
        # A. Delete Historical Data (Pre-Today)
        # We assume the user wants to keep TODAY's orders/transfers, but delete everything before.
        d1, _ = ManufacturingOrder.objects.filter(start_date__lt=today).delete()
        d2, _ = WorkshopTransfer.objects.filter(date__lt=today).delete()
        d3, _ = WorkshopSettlement.objects.filter(date__lt=today).delete()
        print(f"   تم حذف {d1+d2+d3} سجل قديم للورش.")

        # B. Zero Out All Balances
        Workshop.objects.update(
            gold_balance_18=0, gold_balance_21=0, gold_balance_24=0,
            filings_balance_18=0, filings_balance_21=0, filings_balance_24=0,
            labor_balance=0
        )

        # C. Re-Apply Today's Activity
        # 1. Transfers
        for t in WorkshopTransfer.objects.filter(date=today, status='completed'):
            field = 'gold_balance_18'
            if '21' in t.carat.name: field = 'gold_balance_21'
            elif '24' in t.carat.name: field = 'gold_balance_24'
            
            # Source Deduct
            setattr(t.from_workshop, field, getattr(t.from_workshop, field) - t.weight)
            t.from_workshop.save()
            # Dest Add
            setattr(t.to_workshop, field, getattr(t.to_workshop, field) + t.weight)
            t.to_workshop.save()

        # 2. Manufacturing Orders
        # Active (Input added to balance)
        for o in ManufacturingOrder.objects.filter(start_date=today).exclude(status='draft'):
            field = 'gold_balance_18'
            if '21' in o.carat.name: field = 'gold_balance_21'
            elif '24' in o.carat.name: field = 'gold_balance_24'
            setattr(o.workshop, field, getattr(o.workshop, field) + o.input_weight)
            o.workshop.save()

        # Completed (Consumption deducted)
        for o in ManufacturingOrder.objects.filter(end_date=today, status='completed'):
            field = 'gold_balance_18'
            if '21' in o.carat.name: field = 'gold_balance_21'
            elif '24' in o.carat.name: field = 'gold_balance_24'
            
            consumption = (o.output_weight - o.total_stone_weight) + o.scrap_weight + (o.powder_weight or 0)
            is_laser = 'ليزر' in o.workshop.name or 'Laser' in o.workshop.name
            if is_laser and o.output_weight > o.input_weight:
                 consumption = o.input_weight + o.scrap_weight + (o.powder_weight or 0)

            setattr(o.workshop, field, getattr(o.workshop, field) - consumption)
            
            # Add Powder
            p_field = field.replace('gold', 'filings')
            setattr(o.workshop, p_field, getattr(o.workshop, p_field) + (o.powder_weight or 0))
            o.workshop.save()

        print("✅ تم إعادة بناء أرصدة الورش بناءً على حركات اليوم.")


if __name__ == '__main__':
    run()
