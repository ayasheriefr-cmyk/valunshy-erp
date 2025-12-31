from django.core.management.base import BaseCommand
from finance.models import Account, FinanceSettings

class Command(BaseCommand):
    help = 'Setup professional Egyptian Gold Industry Chart of Accounts'

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up professional Egyptian Gold Industry COA...")

        # -- Helper to create or update account --
        def create_acc(code, name, acc_type, parent=None):
            acc, created = Account.objects.update_or_create(
                code=code, 
                defaults={"name": name, "account_type": acc_type, "parent": parent}
            )
            return acc

        # 1. ASSETS (الأصول)
        assets = create_acc("1", "الأصول", "asset")
        
        # 11 Current Assets (الأصول المتداولة)
        curr_assets = create_acc("11", "الأصول المتداولة", "asset", assets)
        cash = create_acc("1101", "الخزينة الرئيسية (نقدية)", "asset", curr_assets)
        banks = create_acc("1102", "الحسابات البنكية / مدى", "asset", curr_assets)
        
        # Gold Stock (مخزون الذهب)
        inventory = create_acc("1103", "مخزون الذهب بضاعة تامة", "asset", curr_assets)
        create_acc("110318", "مخزون ذهب عيار 18", "asset", inventory)
        create_acc("110321", "مخزون ذهب عيار 21", "asset", inventory)
        create_acc("110324", "مخزون ذهب عيار 24 (سبائك)", "asset", inventory)
        
        # Work in Progress
        create_acc("1104", "ذهب قيد التصنيع (لدى الورش)", "asset", curr_assets)
        create_acc("1105", "مخزون الذهب الكسر / المستعمل", "asset", curr_assets)
        create_acc("1106", "عملاء ومبالغ مدينة", "asset", curr_assets)

        # 2. LIABILITIES (الخصوم)
        liabilities = create_acc("2", "الخصوم والالتزامات", "liability")
        curr_liab = create_acc("21", "الخصوم المتداولة", "liability", liabilities)
        create_acc("2101", "موردي الذهب (موازين)", "liability", curr_liab)
        create_acc("2102", "موردي المصنعيات والخدمات", "liability", curr_liab)
        vat_payable = create_acc("2103", "ضريبة القيمة المضافة", "liability", curr_liab)

        # 3. EQUITY (حقوق الملكية)
        equity = create_acc("3", "حقوق الملكية", "equity")
        create_acc("3101", "رأس المال", "equity", equity)
        create_acc("3102", "الأرباح المرحلة", "equity", equity)

        # 4. REVENUE (الإيرادات)
        revenue = create_acc("4", "الإيرادات", "revenue")
        sales_rev = create_acc("41", "إيرادات المبيعات", "revenue", revenue)
        create_acc("4101", "إيرادات المصنعيات (شغل)", "revenue", sales_rev)
        create_acc("4102", "إيرادات بيع الذهب", "revenue", sales_rev)
        create_acc("4103", "إيرادات فصوص وإكسسوارات", "revenue", sales_rev)

        # 5. EXPENSES (المصروفات)
        expenses = create_acc("5", "المصروفات", "expense")
        cog = create_acc("51", "تكلفة البضاعة المباعة", "expense", expenses)
        
        # Important for Gold: Scrap and Loss
        create_acc("52", "مصاريف التصنيع والهالك (الخسية)", "expense", expenses)
        create_acc("53", "مصاريف عمومية وإدارية", "expense", expenses)
        create_acc("5301", "رواتب وأجور", "expense", expenses)
        create_acc("5302", "إيجارات ومرافق", "expense", expenses)
        create_acc("5303", "عمولات مناديب المبيعات", "expense", expenses)

        self.stdout.write("COA created/updated successfully.")

        # 2. Link in Finance Settings
        settings, _ = FinanceSettings.objects.get_or_create(pk=1)
        settings.cash_account = cash
        settings.sales_revenue_account = sales_rev
        settings.inventory_gold_account = inventory
        settings.vat_account = vat_payable
        settings.cost_of_gold_account = cog
        settings.save()

        self.stdout.write(self.style.SUCCESS("Accounting defaults finalized."))
