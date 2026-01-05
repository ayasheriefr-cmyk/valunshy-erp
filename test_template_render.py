import os
import django
from django.template.loader import render_to_string
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

context = {
    'title': 'Test Dashboard',
    'today': '2026-01-05',
    'totals': {
        'cash': Decimal('1000.00'),
        'gold_21': Decimal('100.000'),
        'gold_18': Decimal('200.000'),
        'gold_24': Decimal('50.000'),
        'gold_casting': Decimal('10.000'),
        'stones': Decimal('5.000'),
    },
    'treasury_data': [
        {
            'treasury': {'name': 'الخزينة الرئيسية', 'get_treasury_type_display': 'N/A'},
            'cash_balance': Decimal('500.00'),
            'total_gold': Decimal('150.000'),
            'gold_21': Decimal('100.000'),
            'gold_18': Decimal('50.000'),
            'cash_in_today': Decimal('100.00'),
            'cash_out_today': Decimal('20.00'),
            'net_today': Decimal('80.00'),
        }
    ],
    'recent_transfers': []
}

try:
    html = render_to_string('finance/treasuries_dashboard.html', context)
    print("Success: Template rendered without SyntaxError.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
