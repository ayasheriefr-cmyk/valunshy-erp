import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import Workshop, Stone

def reset_all_balances():
    print("=== Start Resetting Manufacturing Balances ===")
    
    # 1. Reset Workshop Balances
    print("Resetting all Workshop balances (Gold, Scrap, Powder, Labor)...")
    workshops = Workshop.objects.all()
    count_ws = workshops.count()
    for ws in workshops:
        ws.gold_balance_18 = Decimal('0')
        ws.gold_balance_21 = Decimal('0')
        ws.gold_balance_24 = Decimal('0')
        
        ws.scrap_balance_18 = Decimal('0')
        ws.scrap_balance_21 = Decimal('0')
        ws.scrap_balance_24 = Decimal('0')
        
        ws.filings_balance_18 = Decimal('0')
        ws.filings_balance_21 = Decimal('0')
        ws.filings_balance_24 = Decimal('0')
        
        ws.labor_balance = Decimal('0')
        ws.save()
    print(f"Successfully reset balances for {count_ws} workshops.")

    # 2. Reset Stone Inventory
    print("Resetting all Stone stocks...")
    stones = Stone.objects.all()
    count_stones = stones.count()
    for stone in stones:
        stone.current_stock = Decimal('0')
        stone.current_quantity = 0
        stone.save()
    print(f"Successfully reset stocks for {count_stones} stones.")

    print("\n[SUCCESS] All balances have been reset to zero.")

if __name__ == "__main__":
    reset_all_balances()
