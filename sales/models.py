from django.db import models
from django.utils.translation import gettext_lazy as _
from inventory.models import Item, Branch, Carat
from crm.models import Customer
from django.conf import settings

class Reservation(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='reservation', verbose_name="القطعة")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reservations', verbose_name="العميل")
    sales_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="المندوب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الحجز")
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "حجز"
        verbose_name_plural = "الحجوزات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item.name} - {self.customer.name}"

class Invoice(models.Model):
    invoice_number = models.CharField("رقم الفاتورة", max_length=50, unique=True)
    customer = models.ForeignKey('crm.Customer', on_delete=models.SET_NULL, null=True, related_name='invoices', verbose_name="العميل")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع")
    
    # Financial Totals
    total_gold_value = models.DecimalField("قيمة الذهب", max_digits=12, decimal_places=2, default=0)
    total_labor_value = models.DecimalField("قيمة المصنعية", max_digits=12, decimal_places=2, default=0)
    total_stones_value = models.DecimalField("قيمة الأحجار", max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField("ضريبة القيمة المضافة", max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField("الإجمالي النهائي", max_digits=12, decimal_places=2, default=0)
    
    # Gold Exchange
    is_exchange = models.BooleanField(_("Is Exchange?"), default=False)
    exchange_gold_weight = models.DecimalField(_("Exchange Gold Weight"), max_digits=10, decimal_places=3, default=0)
    exchange_value_deducted = models.DecimalField(_("Exchange Value Deducted"), max_digits=12, decimal_places=2, default=0)

    payment_method_choices = [
        ('cash', 'نقدي'),
        ('card', 'بطاقة / مدى'),
        ('bank_transfer', 'تحويل بنكي'),
        ('mixed', 'دفع مختلط'),
    ]
    payment_method = models.CharField("طريقة الدفع", max_length=20, choices=payment_method_choices, default='cash')
    
    # ZATCA fields (Simplified for now)
    zatca_uuid = models.UUIDField("ZATCA UUID", null=True, blank=True)
    zatca_qr_code = models.TextField("ZATCA QR Code", blank=True)
    
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True, db_index=True)
    created_by = models.ForeignKey('auth.User', verbose_name="أنشئ بواسطة", on_delete=models.PROTECT)
    sales_rep = models.ForeignKey('SalesRepresentative', on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name="المندوب", related_name='invoices')

    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('pending', 'قيد المراجعة (انتظار التأكيد)'),
        ('confirmed', 'تم التأكيد (نشط ماليًا)'),
        ('rejected', 'مرفوض'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    confirmed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name="تم التأكيد بواسطة", related_name='confirmed_invoices')
    confirmed_at = models.DateTimeField("تاريخ التأكيد", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Prevent recursion and only calculate if instance already exists (pk is set)
        if self.pk and not kwargs.get('update_fields'):
             self.calculate_totals(save=False)
        super().save(*args, **kwargs)

    @property
    def total_profit(self):
        """إجمالي ربح الفاتورة"""
        return sum(item.profit for item in self.items.all())
    
    def calculate_totals(self, save=True):
        """
        إعادة حساب كافة المبالغ المالية للفاتورة
        """
        from decimal import Decimal
        
        items = self.items.all()
        
        total_gold = Decimal('0')
        total_labor = Decimal('0')
        total_stones = Decimal('0')
        
        for item in items:
            total_gold += (item.sold_weight * item.sold_gold_price)
            total_labor += item.sold_labor_fee
            total_stones += item.sold_stone_fee
            
        self.total_gold_value = total_gold
        self.total_labor_value = total_labor
        self.total_stones_value = total_stones
        
        # Aggregate Exchange (Old Gold Return)
        if self.is_exchange:
            from django.db.models import Sum
            exch_totals = self.returned_gold.aggregate(
                w=Sum('weight'), v=Sum('value')
            )
            self.exchange_gold_weight = exch_totals['w'] or Decimal('0')
            self.exchange_value_deducted = exch_totals['v'] or Decimal('0')
        else:
            self.exchange_gold_weight = Decimal('0')
            self.exchange_value_deducted = Decimal('0')

        # Tax Calculation (15% VAT on Net Sale)
        net_sale = total_gold + total_labor + total_stones
        self.total_tax = (net_sale * Decimal('0.15')).quantize(Decimal('0.01'))
        
        # Grand Total
        self.grand_total = net_sale + self.total_tax
        
        if save:
            self.save(update_fields=[
                'total_gold_value', 'total_labor_value', 'total_stones_value', 
                'total_tax', 'grand_total', 'exchange_gold_weight', 'exchange_value_deducted'
            ])
        
        return self.grand_total

    class Meta:
        verbose_name = "فاتورة مبيعات"
        verbose_name_plural = "سجل فواتير المبيعات"

    def __str__(self):
        return self.invoice_number

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    
    # Snapshot of values at time of sale
    sold_weight = models.DecimalField("الوزن المباع", max_digits=10, decimal_places=3)
    sold_gold_price = models.DecimalField("سعر الذهب وقت البيع", max_digits=10, decimal_places=2)
    sold_labor_fee = models.DecimalField("أجر المصنعية (المحصل)", max_digits=10, decimal_places=2)
    sold_stone_fee = models.DecimalField("قيمة الفصوص/الأحجار", max_digits=10, decimal_places=2, default=0)
    sold_factory_cost = models.DecimalField("تكلفة المصنع (أجور + مصاريف)", max_digits=10, decimal_places=2, default=0, help_text="إجمالي التكلفة الصناعية المخزنة في القطعة وقت البيع")
    
    subtotal = models.DecimalField("إجمالي السطر", max_digits=12, decimal_places=2)

    @property
    def total_cost(self):
        """إجمالي تكلفة السطر = (ذهب × سعر الشراء/البيع المرجعي) + تكلفة المصنع"""
        # Note: In gold retail, cost is often (Net Gold Weight * current price) + manufacturing
        # Here we use the price recorded at sale for the gold component
        gold_cost = (self.item.net_gold_weight * self.sold_gold_price)
        return gold_cost + self.sold_factory_cost + self.sold_stone_fee

    @property
    def profit(self):
        """الربح = الإجمالي - التكلفة"""
        return self.subtotal - self.total_cost
    
    def save(self, *args, **kwargs):
        # Capture the manufacturing cost snapshot (Labor + Overheads) at the moment of sale
        if self.item:
            if not self.sold_factory_cost or self.sold_factory_cost == 0:
                self.sold_factory_cost = self.item.total_manufacturing_cost
            
            # Auto-populate stone fee from item default if not set
            if not self.sold_stone_fee or self.sold_stone_fee == 0:
                self.sold_stone_fee = self.item.default_stone_fee

        # Ensure subtotal is calculated before save
        self.subtotal = (self.sold_weight * self.sold_gold_price) + self.sold_labor_fee + self.sold_stone_fee
        
        super().save(*args, **kwargs)
        
        # Trigger invoice recalculation
        if self.invoice:
            self.invoice.calculate_totals()

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.item.barcode}"

class OldGoldReturn(models.Model):
    """ Used for Gold Exchange """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='returned_gold')
    carat = models.ForeignKey(Carat, on_delete=models.PROTECT)
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    value = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "ذهب مستبدل"
        verbose_name_plural = "المبادلات - الذهب المستعمل"

    def __str__(self):
        return f"تبديل: {self.weight} جرام - {self.carat.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.invoice:
            self.invoice.calculate_totals()


class SalesRepresentative(models.Model):
    """مندوب المبيعات"""
    name = models.CharField("اسم المندوب", max_length=100)
    phone = models.CharField("رقم الهاتف", max_length=20, blank=True)
    email = models.EmailField("البريد الإلكتروني", blank=True)
    address = models.CharField("العنوان", max_length=500, blank=True, null=True)
    user = models.OneToOneField('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="حساب المستخدم المرتبط", help_text="لتمكين الدخول من التطبيق")
    
    # Commission Structure
    commission_type_choices = [
        ('percentage', 'نسبة مئوية'),
        ('fixed', 'مبلغ ثابت'),
    ]
    commission_type = models.CharField("نوع العمولة", max_length=20, choices=commission_type_choices, default='percentage')
    commission_rate = models.DecimalField("نسبة/قيمة العمولة", max_digits=10, decimal_places=2, default=0, 
                                          help_text="إذا كانت نسبة مئوية، أدخل القيمة (مثال: 2.5 تعني 2.5%)")
    
    # Assignment
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الفرع المسؤول عنه")
    is_active = models.BooleanField("نشط", default=True)
    
    # Performance Tracking
    total_sales = models.DecimalField("إجمالي المبيعات", max_digits=15, decimal_places=2, default=0)
    total_commission = models.DecimalField("إجمالي العمولات", max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "مندوب مبيعات"
        verbose_name_plural = "المبيعات - المندوبين"
    
    def __str__(self):
        return self.name
    
    def calculate_commission(self, sale_amount):
        """حساب العمولة على مبلغ معين"""
        if self.commission_type == 'percentage':
            return (sale_amount * self.commission_rate) / 100
        return self.commission_rate


class SalesRepTransaction(models.Model):
    """حركات المندوب"""
    sales_rep = models.ForeignKey(SalesRepresentative, on_delete=models.CASCADE, related_name='transactions', verbose_name="المندوب")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الفاتورة")
    
    transaction_type_choices = [
        ('commission', 'عمولة'),
        ('bonus', 'مكافأة'),
        ('deduction', 'خصم'),
        ('payment', 'صرف'),
    ]
    transaction_type = models.CharField("نوع الحركة", max_length=20, choices=transaction_type_choices)
    
    amount = models.DecimalField("المبلغ", max_digits=12, decimal_places=2)
    notes = models.TextField("ملاحظات", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "حركة مندوب"
        verbose_name_plural = "المبيعات - حركات المندوبين"
    
    def __str__(self):
        return f"{self.sales_rep.name} - {self.get_transaction_type_display()} - {self.amount}"

