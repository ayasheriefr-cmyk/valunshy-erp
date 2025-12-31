import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from manufacturing.models import Workshop
from django.db.models import Sum

ws = Workshop.objects.all()
g18 = ws.aggregate(Sum('gold_balance_18'))['gold_balance_18__sum'] or 0
g21 = ws.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0
g24 = ws.aggregate(Sum('gold_balance_24'))['gold_balance_24__sum'] or 0
print(f"18k: {g18}")
print(f"21k: {g21}")
print(f"24k: {g24}")
print(f"Combined: {g18 + g21 + g24}")
