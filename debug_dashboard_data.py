import os
import django
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from inventory.models import Item, RawMaterial
from finance.treasury_models import Treasury
from core.models import GoldPrice

print("--- DEBUGGING DATA ---")

# Check Items
item_count = Item.objects.count()
item_weight = Item.objects.aggregate(Sum('net_gold_weight'))['net_gold_weight__sum']
print(f"Items Count: {item_count}")
print(f"Items Total Weight: {item_weight}")

# Check Raw Materials
raw_count = RawMaterial.objects.count()
raw_weight = RawMaterial.objects.aggregate(Sum('current_weight'))['current_weight__sum']
print(f"Raw Materials Count: {raw_count}")
print(f"Raw Materials Weight: {raw_weight}")

# Check Treasury
treasury_count = Treasury.objects.count()
treasury_gold = Treasury.objects.aggregate(
    g18=Sum('gold_balance_18'),
    g21=Sum('gold_balance_21'),
    g24=Sum('gold_balance_24'),
    casting=Sum('gold_casting_balance')
)
print(f"Treasury Count: {treasury_count}")
print(f"Treasury Gold: {treasury_gold}")

# Check Gold Price
price_21 = GoldPrice.objects.filter(carat__name__icontains='21').first()
print(f"Price 21k: {price_21.price_per_gram if price_21 else 'Not Found'}")
