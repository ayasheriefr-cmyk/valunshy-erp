import os
import django
import sys

# Ensure UTF-8 output for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop
from finance.treasury_models import Treasury

def check_balances():
    try:
        ws6 = Workshop.objects.get(id=6)
        ws12 = Workshop.objects.get(id=12)
        t5 = Treasury.objects.get(id=5)
        
        print(f"Workshop 6 (ID 6): {ws6.name}")
        print(f"  Gold 18: {ws6.gold_balance_18}")
        print(f"  Gold 21: {ws6.gold_balance_21}")
        print(f"  Gold 24: {ws6.gold_balance_24}")
        
        print(f"\nWorkshop 12 (ID 12): {ws12.name}")
        print(f"  Gold 18: {ws12.gold_balance_18}")
        print(f"  Gold 21: {ws12.gold_balance_21}")
        print(f"  Gold 24: {ws12.gold_balance_24}")
        
        print(f"\nTreasury 5 (ID 5): {t5.name}")
        print(f"  Gold 18: {t5.gold_balance_18}")
        print(f"  Gold 21: {t5.gold_balance_21}")
        print(f"  Gold 24: {t5.gold_balance_24}")
        print(f"  Linked Workshop: {t5.workshop}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_balances()
