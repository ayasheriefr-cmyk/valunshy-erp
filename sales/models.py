from django.db import models
from django.utils.translation import gettext_lazy as _
from inventory.models import Item, Branch, Carat
from crm.models import Customer # Will create this next

class Invoice(models.Model):
    invoice_number = models.CharField("رقم الفاتورة", max_length=50, unique=True)
    customer = models.ForeignKey('crm.Customer', on_delete=models.SET_NULL, null=True, related_name='invoices', verbose_name="العميل")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="الفرع")
    
    # Financial Totals
    total_gold_value = models.DecimalField("قيمة الذهب", max_digits=12, decimal_places=2, default=0)
    total_labor_value = models.DecimalField("قيمة المصنعية", max_digits=12, decimal_places=2, default=0)
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
    
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
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

    class Meta:
        verbose_name = "فاتورة مبيعات"
        verbose_name_plural = "سجل فواتير المبيعات"

    def __str__(self):
        return self.invoice_number

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    
    # Snapshot of values at time of sale
    sold_weight = models.DecimalField(max_digits=10, decimal_places=3)
    sold_gold_price = models.DecimalField(max_digits=10, decimal_places=2)
    sold_labor_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

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


class SalesRepresentative(models.Model):
    """مندوب المبيعات"""
    name = models.CharField("اسم المندوب", max_length=100)
    phone = models.CharField("رقم الهاتف", max_length=20, blank=True)
    email = models.EmailField("البريد الإلكتروني", blank=True)
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

