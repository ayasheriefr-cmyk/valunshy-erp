from django.core.management.base import BaseCommand
from core.models import Carat, Branch
from finance.models import Account, FinanceSettings

class Command(BaseCommand):
    help = 'Initialize basic gold data and chart of accounts'

    def handle(self, *args, **kwargs):
        self.stdout.write("Initializing Gold ERP Data...")

        # 1. Carats
        carats = [
            {'name': '24K', 'purity': 1.0000},
            {'name': '22K', 'purity': 0.9167},
            {'name': '21K', 'purity': 0.8750},
            {'name': '18K', 'purity': 0.7500},
        ]
        for c in carats:
            Carat.objects.get_or_create(name=c['name'], defaults={'purity': c['purity']})

        # 2. Main Branch
        branch, _ = Branch.objects.get_or_create(name="Main Store (المركز الرئيسي)", defaults={'is_main': True})

        # 3. Chart of Accounts (Basic)
        accounts = [
            {'code': '1101', 'name': 'Cash on Hand (الصندوق)', 'type': 'asset'},
            {'code': '1201', 'name': 'Gold Inventory (مخزون الذهب)', 'type': 'asset'},
            {'code': '2101', 'name': 'VAT Payable (ضريبة القيمة المضافة)', 'type': 'liability'},
            {'code': '4101', 'name': 'Sales Revenue (إيرادات المبيعات)', 'type': 'revenue'},
            {'code': '5101', 'name': 'Cost of Gold Sold (تكلفة الذهب)', 'type': 'expense'},
        ]
        acc_objs = {}
        for a in accounts:
            obj, _ = Account.objects.get_or_create(code=a['code'], defaults={'name': a['name'], 'account_type': a['type']})
            acc_objs[a['code']] = obj

        # 4. Finance Settings
        FinanceSettings.objects.get_or_create(pk=1, defaults={
            'cash_account': acc_objs['1101'],
            'sales_revenue_account': acc_objs['4101'],
            'inventory_gold_account': acc_objs['1201'],
            'cost_of_gold_account': acc_objs['5101'],
            'vat_account': acc_objs['2101'],
        })

        self.stdout.write(self.style.SUCCESS("Successfully initialized Gold ERP system defaults."))
