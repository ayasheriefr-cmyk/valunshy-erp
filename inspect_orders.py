
import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from manufacturing.models import ManufacturingOrder

def inspect():
    print("Latest 20 Orders:")
    try:
        orders = ManufacturingOrder.objects.all().order_by('-id')[:20]
        for o in orders:
            ws_name = o.workshop.name if o.workshop else "None"
            try:
                print(f"ID: {o.id} | No: {o.order_number} | Status: {o.status} | Workshop: {ws_name}")
            except UnicodeEncodeError:
                print(f"ID: {o.id} | No: {o.order_number} | Status: {o.status} | Workshop: (Arabic Name)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    inspect()
