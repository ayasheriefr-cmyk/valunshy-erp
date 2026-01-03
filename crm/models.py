from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import Carat

class Customer(models.Model):
    name = models.CharField(_("Customer Name"), max_length=255)
    phone = models.CharField(_("Phone Number"), max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    vat_number = models.CharField(_("VAT Number"), max_length=50, blank=True, null=True)
    
    # App Login
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='customer_profile', verbose_name='حساب التطبيق')
    
    # Preferences & Special Occasions
    birth_date = models.DateField(blank=True, null=True)
    wedding_anniversary = models.DateField(blank=True, null=True)
    
    # Financial Balances
    money_balance = models.DecimalField("الرصيد النقدي", max_digits=15, decimal_places=2, default=0, help_text="الرصيد المدين/الدائن للعميل")
    
    # Gold Balances (Custody or savings)
    gold_balance_18 = models.DecimalField("رصيد ذهب 18 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_21 = models.DecimalField("رصيد ذهب 21 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_24 = models.DecimalField("رصيد ذهب 24 (جم)", max_digits=12, decimal_places=3, default=0)
    
    total_purchases_value = models.DecimalField("إجمالي المشتريات", max_digits=15, decimal_places=2, default=0)
    loyalty_points = models.IntegerField("نقاط الولاء", default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"
    
    def update_balances(self):
        """إعادة حساب الأرصدة بناءً على الحركات"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Cash Balance
        totals = self.ledger_transactions.aggregate(
            total_debit=Sum('cash_debit'),
            total_credit=Sum('cash_credit')
        )
        self.money_balance = (totals['total_credit'] or Decimal('0')) - (totals['total_debit'] or Decimal('0'))
        
        # Gold Balances
        for carat_val in [18, 21, 24]:
            gold_totals = self.ledger_transactions.filter(carat__base_weight=carat_val).aggregate(
                total_gold_debit=Sum('gold_debit'),
                total_gold_credit=Sum('gold_credit')
            )
            balance = (gold_totals['total_gold_credit'] or Decimal('0')) - (gold_totals['total_gold_debit'] or Decimal('0'))
            setattr(self, f'gold_balance_{carat_val}', balance)
            
        self.save(update_fields=['money_balance', 'gold_balance_18', 'gold_balance_21', 'gold_balance_24'])

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "بيانات العملاء"

class CustomerTransaction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='ledger_transactions', verbose_name="العميل")
    
    TRANSACTION_TYPES = [
        ('sale', 'مبيعات'),
        ('payment', 'دفع نقدي'),
        ('gold_in', 'إيداع ذهب'),
        ('gold_out', 'صرف ذهب'),
        ('barter', 'مقايضة'),
        ('khasia', 'خسية/خصم'),
        ('adjustment', 'تسوية رصيد'),
    ]
    transaction_type = models.CharField("نوع الحركة", max_length=20, choices=TRANSACTION_TYPES)
    
    cash_debit = models.DecimalField("مدين (عليه)", max_digits=15, decimal_places=2, default=0, help_text="المبالغ المستحقة على العميل")
    cash_credit = models.DecimalField("دائن (له)", max_digits=15, decimal_places=2, default=0, help_text="المبالغ المدفوعة من العميل")
    
    gold_debit = models.DecimalField("وزن مدين (سحب)", max_digits=15, decimal_places=3, default=0, help_text="وزن الذهب الذي استلمه العميل")
    gold_credit = models.DecimalField("وزن دائن (إيداع)", max_digits=15, decimal_places=3, default=0, help_text="وزن الذهب الذي قدمه العميل (كسر/مقايضة)")
    carat = models.ForeignKey(Carat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="العيار")
    
    invoice = models.ForeignKey('sales.Invoice', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الفاتورة المرتبطة")
    
    date = models.DateField("تاريخ الحركة", default=timezone.now)
    description = models.TextField("البيان / الوصف", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "حركة حساب عميل"
        verbose_name_plural = "حركات حسابات العملاء"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.get_transaction_type_display()} - {self.date}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
             self.customer.update_balances()

class Supplier(models.Model):
    name = models.CharField("اسم المورد", max_length=255)
    phone = models.CharField("رقم الجوال", max_length=20, blank=True)
    contact_person = models.CharField("الشخص المسؤول", max_length=100, blank=True)
    email = models.EmailField("البريد الإلكتروني", blank=True, null=True)
    vat_number = models.CharField("الرقم الضريبي", max_length=50, blank=True, null=True)
    address = models.CharField("العنوان", max_length=500, blank=True)
    primary_carat = models.IntegerField("العيار الأساسي", default=18, help_text="العيار الذي يتم التعامل به غالباً")
    
    SUPPLIER_TYPE_CHOICES = [
        ('gold_office', 'مكتب ذهب'),
        ('factory', 'مصنع'),
        ('trader', 'تاجر كسر'),
        ('other', 'آخر'),
    ]
    supplier_type = models.CharField("نوع المورد", max_length=20, choices=SUPPLIER_TYPE_CHOICES, default='factory')

    # Financial Balances
    money_balance = models.DecimalField("الرصيد النقدي", max_digits=15, decimal_places=2, default=0, help_text="الرصيد المدين/الدائن للمورد")
    
    # Gold Balances (Custody or debts)
    gold_balance_18 = models.DecimalField("رصيد ذهب 18 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_21 = models.DecimalField("رصيد ذهب 21 (جم)", max_digits=12, decimal_places=3, default=0)
    gold_balance_24 = models.DecimalField("رصيد ذهب 24 (جم)", max_digits=12, decimal_places=3, default=0)
    
    notes = models.TextField("ملاحظات", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_supplier_type_display()})"

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "الموردين"

    def update_balances(self):
        """إعادة حساب أرصدة المورد بناءً على الحركات"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Cash Balance
        totals = self.ledger_transactions.aggregate(
            total_debit=Sum('cash_debit'),
            total_credit=Sum('cash_credit')
        )
        # الرصيد = الدائن (له) - المدين (عليه)
        # للمورد: "له" يعني ورد لنا بضاعة، "عليه" يعني استلم منا دفعة
        self.money_balance = (totals['total_credit'] or Decimal('0')) - (totals['total_debit'] or Decimal('0'))
        
        # Gold Balances
        for carat_val in [18, 21, 24]:
            gold_totals = self.ledger_transactions.filter(carat__base_weight=carat_val).aggregate(
                total_gold_debit=Sum('gold_debit'),
                total_gold_credit=Sum('gold_credit')
            )
            # رصيد الذهب بنفس المنطقة: له (إيداع/شراء منه) - عليه (سحب/بيع له)
            balance = (gold_totals['total_gold_credit'] or Decimal('0')) - (gold_totals['total_gold_debit'] or Decimal('0'))
            setattr(self, f'gold_balance_{carat_val}', balance)
            
        self.save(update_fields=['money_balance', 'gold_balance_18', 'gold_balance_21', 'gold_balance_24'])


class SupplierTransaction(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='ledger_transactions', verbose_name="المورد")
    
    TRANSACTION_TYPES = [
        ('purchase', 'مشتريات/توريد'),
        ('payment', 'دفعة نقدية (له)'),
        ('return_cash', 'رد نقدية (منه)'),
        ('gold_in', 'توريد ذهب (له)'),
        ('gold_out', 'صرف ذهب (عليه)'),
        ('adjustment', 'تسوية رصيد'),
    ]
    transaction_type = models.CharField("نوع الحركة", max_length=20, choices=TRANSACTION_TYPES)
    
    cash_debit = models.DecimalField("مدين (عليه)", max_digits=15, decimal_places=2, default=0, help_text="المبالغ التي استلمها المورد (دفعة)")
    cash_credit = models.DecimalField("دائن (له)", max_digits=15, decimal_places=2, default=0, help_text="قيمة البضاعة الموردة")
    
    gold_debit = models.DecimalField("وزن مدين (سحب)", max_digits=15, decimal_places=3, default=0, help_text="وزن أخذه المورد")
    gold_credit = models.DecimalField("وزن دائن (إيداع)", max_digits=15, decimal_places=3, default=0, help_text="وزن ورده المورد")
    carat = models.ForeignKey(Carat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="العيار")
    
    date = models.DateField("تاريخ الحركة", default=timezone.now)
    description = models.TextField("البيان / الوصف", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "حركة حساب مورد"
        verbose_name_plural = "حركات حسابات الموردين"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.supplier.name} - {self.get_transaction_type_display()} - {self.date}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
             self.supplier.update_balances()

