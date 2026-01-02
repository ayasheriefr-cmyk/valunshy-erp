"""
نظام الخزينة والعهد المتكامل
Treasury and Custody Management System
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class Treasury(models.Model):
    """الخزائن - يمكن أن يكون هناك أكثر من خزينة"""
    name = models.CharField("اسم الخزينة", max_length=100)
    code = models.CharField("كود الخزينة", max_length=20, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='sub_treasuries', verbose_name="الخزينة الأم")
    
    TREASURY_TYPE_CHOICES = [
        ('main', 'الخزينة الرئيسية'),
        ('branch', 'خزينة فرع'),
        ('petty', 'خزينة مصروفات نثرية'),
        ('sales', 'خزينة مبيعات'),
        ('workshop', 'خزينة ورشة'),
        ('gold_raw', 'خزينة ذهب خام (للسبك)'),
        ('stones', 'خزينة أحجار للتصنيع'),
        ('finished', 'خزينة إنتاج تام'),
        ('gold_tools', 'خزينة أدوات تصنيع (ذهب)'),
        ('production', 'خزينة قسم الإنتاج'),
        ('casting', 'خزينة قسم السبك'),
        ('laser_powder', 'خزينة بودر ليزر'),
        ('laser_scrap', 'خزينة خسية الليزر'),
        ('casting_powder', 'خزينة بودر سبك'),
        ('casting_scrap', 'خزينة خسية سبك'),
        ('laser', 'خزينة ليزر'),
    ]
    treasury_type = models.CharField("نوع الخزينة", max_length=20, choices=TREASURY_TYPE_CHOICES, default='main')
    
    # الأرصدة الحالية
    cash_balance = models.DecimalField("رصيد النقدية", max_digits=15, decimal_places=2, default=0)
    gold_balance_18 = models.DecimalField("رصيد ذهب 18", max_digits=15, decimal_places=3, default=0)
    gold_balance_21 = models.DecimalField("رصيد ذهب 21", max_digits=15, decimal_places=3, default=0)
    gold_balance_24 = models.DecimalField("رصيد ذهب 24", max_digits=15, decimal_places=3, default=0)
    
    # مخازن التصنيع (Gold for Casting & Stones)
    gold_casting_balance = models.DecimalField("رصيد ذهب للسبك", max_digits=15, decimal_places=3, default=0)
    stones_balance = models.DecimalField("رصيد أحجار للتصنيع", max_digits=15, decimal_places=3, default=0)
    
    # المسؤول
    responsible_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                         verbose_name="مسؤول الخزينة", related_name='treasuries')
    
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True, 
                               verbose_name="الفرع")
    
    is_active = models.BooleanField("نشطة", default=True)
    
    # Link to Accounting
    linked_account = models.ForeignKey('finance.Account', on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name="الحساب المالي المرتبط", help_text="الحساب الذي سيتم التأثير عليه في قيود اليومية")

    # Link to Workshop
    workshop = models.ForeignKey('manufacturing.Workshop', on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="الورشة المرتبطة", related_name='treasuries')

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "خزينة"
        verbose_name_plural = "الخزينة - الخزائن"
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def total_gold_balance(self):
        """إجمالي رصيد الذهب بالجرام"""
        return self.gold_balance_18 + self.gold_balance_21 + self.gold_balance_24


class TreasuryTransaction(models.Model):
    """حركات الخزينة"""
    treasury = models.ForeignKey(Treasury, on_delete=models.CASCADE, related_name='transactions',
                                 verbose_name="الخزينة")
    
    TRANSACTION_TYPE_CHOICES = [
        ('cash_in', 'إيداع نقدي'),
        ('cash_out', 'صرف نقدي'),
        ('gold_in', 'إيداع ذهب'),
        ('gold_out', 'صرف ذهب'),
        ('transfer_in', 'تحويل وارد'),
        ('transfer_out', 'تحويل صادر'),
        ('finished_goods_in', 'وارد إنتاج تام'),
        ('adjustment', 'تسوية'),
    ]
    transaction_type = models.CharField("نوع الحركة", max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    # المبالغ
    cash_amount = models.DecimalField("المبلغ النقدي", max_digits=15, decimal_places=2, default=0)
    gold_weight = models.DecimalField("وزن الذهب", max_digits=15, decimal_places=3, default=0)
    gold_casting_weight = models.DecimalField("وزن ذهب سبك", max_digits=15, decimal_places=3, default=0)
    stones_weight = models.DecimalField("وزن أحجار", max_digits=15, decimal_places=3, default=0)
    gold_carat = models.ForeignKey('core.Carat', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="العيار")
    
    cost_center = models.ForeignKey('finance.CostCenter', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="مركز التكلفة")
    
    # مرجع للعملية
    reference_type = models.CharField("نوع المرجع", max_length=50, blank=True)  # invoice, custody, etc.
    reference_id = models.IntegerField("رقم المرجع", null=True, blank=True)
    
    description = models.TextField("البيان")
    date = models.DateField("التاريخ", default=timezone.now)
    
    # الأرصدة بعد الحركة
    balance_after_cash = models.DecimalField("الرصيد بعد الحركة", max_digits=15, decimal_places=2, default=0)
    balance_after_gold = models.DecimalField("رصيد الذهب بعد الحركة", max_digits=15, decimal_places=3, default=0)
    balance_after_gold_casting = models.DecimalField("رصيد السبك بعد الحركة", max_digits=15, decimal_places=3, default=0)
    balance_after_stones = models.DecimalField("رصيد الأحجار بعد الحركة", max_digits=15, decimal_places=3, default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="أنشئ بواسطة")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "حركة خزينة"
        verbose_name_plural = "الخزينة - الحركات"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.date}"


class CustodyHolder(models.Model):
    """مستلمي العهد"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='custody_profile',
                                verbose_name="المستخدم")
    
    HOLDER_TYPE_CHOICES = [
        ('employee', 'موظف'),
        ('sales_rep', 'مندوب مبيعات'),
        ('workshop', 'ورشة'),
        ('technician', 'فني'),
    ]
    holder_type = models.CharField("نوع المستلم", max_length=20, choices=HOLDER_TYPE_CHOICES, default='employee')
    
    # حدود العهدة
    max_cash_custody = models.DecimalField("الحد الأقصى للعهدة النقدية", max_digits=15, decimal_places=2, default=0)
    max_gold_custody = models.DecimalField("الحد الأقصى لعهدة الذهب (جرام)", max_digits=15, decimal_places=3, default=0)
    
    # الأرصدة الحالية
    current_cash_custody = models.DecimalField("العهدة النقدية الحالية", max_digits=15, decimal_places=2, default=0)
    current_gold_18 = models.DecimalField("عهدة ذهب 18", max_digits=15, decimal_places=3, default=0)
    current_gold_21 = models.DecimalField("عهدة ذهب 21", max_digits=15, decimal_places=3, default=0)
    current_gold_24 = models.DecimalField("عهدة ذهب 24", max_digits=15, decimal_places=3, default=0)
    
    is_active = models.BooleanField("نشط", default=True)
    notes = models.TextField("ملاحظات", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "مستلم عهدة"
        verbose_name_plural = "الخزينة - مستلمي العهد"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_holder_type_display()})"
    
    @property
    def total_gold_custody(self):
        return self.current_gold_18 + self.current_gold_21 + self.current_gold_24

class Custody(models.Model):
    """سندات العهد"""
    custody_number = models.CharField("رقم سند العهدة", max_length=50, unique=True)
    
    CUSTODY_TYPE_CHOICES = [
        ('cash', 'عهدة نقدية'),
        ('gold', 'عهدة ذهب'),
        ('mixed', 'عهدة مختلطة'),
    ]
    custody_type = models.CharField("نوع العهدة", max_length=20, choices=CUSTODY_TYPE_CHOICES)
    
    treasury = models.ForeignKey(Treasury, on_delete=models.PROTECT, related_name='custodies',
                                 verbose_name="الخزينة")
    holder = models.ForeignKey(CustodyHolder, on_delete=models.PROTECT, related_name='custodies',
                               verbose_name="مستلم العهدة")
    
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('active', 'نشطة'),
        ('partial_settled', 'مسددة جزئياً'),
        ('settled', 'مسددة بالكامل'),
        ('cancelled', 'ملغاة'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    cash_amount = models.DecimalField("المبلغ النقدي", max_digits=15, decimal_places=2, default=0,
                                     validators=[MinValueValidator(Decimal('0'))])
    
    gold_weight_18 = models.DecimalField("وزن ذهب 18", max_digits=15, decimal_places=3, default=0)
    gold_weight_21 = models.DecimalField("وزن ذهب 21", max_digits=15, decimal_places=3, default=0)
    gold_weight_24 = models.DecimalField("وزن ذهب 24", max_digits=15, decimal_places=3, default=0)
    
    settled_cash = models.DecimalField("المسدد نقداً", max_digits=15, decimal_places=2, default=0)
    settled_gold_18 = models.DecimalField("المسدد ذهب 18", max_digits=15, decimal_places=3, default=0)
    settled_gold_21 = models.DecimalField("المسدد ذهب 21", max_digits=15, decimal_places=3, default=0)
    settled_gold_24 = models.DecimalField("المسدد ذهب 24", max_digits=15, decimal_places=3, default=0)
    
    purpose = models.TextField("الغرض من العهدة")
    issue_date = models.DateField("تاريخ الصرف", default=timezone.now)
    due_date = models.DateField("تاريخ الاستحقاق", null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_custodies', verbose_name="اعتمد بواسطة")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_custodies',
                                   verbose_name="أنشئ بواسطة")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "سند عهدة"
        verbose_name_plural = "الخزينة - سندات العهد"
        ordering = ['-issue_date', '-created_at']
        
    def __str__(self):
        return f"{self.custody_number} - {self.holder.user.username}"

    @property
    def total_gold(self):
        return self.gold_weight_18 + self.gold_weight_21 + self.gold_weight_24

    @property
    def remaining_cash(self):
        return self.cash_amount - self.settled_cash

    @property
    def remaining_gold(self):
        return (self.gold_weight_18 + self.gold_weight_21 + self.gold_weight_24) - \
               (self.settled_gold_18 + self.settled_gold_21 + self.settled_gold_24)

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['settled', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False
        
    def save(self, *args, **kwargs):
        if not self.custody_number:
            last = Custody.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.custody_number = f"CUS-{num:05d}"
        super().save(*args, **kwargs)



class CustodySettlement(models.Model):
    """تسويات العهد"""
    custody = models.ForeignKey(Custody, on_delete=models.CASCADE, related_name='settlements',
                                verbose_name="سند العهدة")
    
    SETTLEMENT_TYPE_CHOICES = [
        ('cash_return', 'رد نقدي'),
        ('gold_return', 'رد ذهب'),
        ('invoice_deduction', 'خصم من فاتورة'),
        ('expense_voucher', 'إذن صرف'),
    ]
    settlement_type = models.CharField("نوع التسوية", max_length=20, choices=SETTLEMENT_TYPE_CHOICES)
    
    cash_amount = models.DecimalField("المبلغ النقدي", max_digits=15, decimal_places=2, default=0)
    gold_weight = models.DecimalField("وزن الذهب", max_digits=15, decimal_places=3, default=0)
    gold_carat = models.ForeignKey('core.Carat', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="العيار")
    
    reference = models.CharField("رقم المرجع", max_length=100, blank=True)
    notes = models.TextField("ملاحظات", blank=True)
    date = models.DateField("تاريخ التسوية", default=timezone.now)
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="أنشئ بواسطة")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "تسوية عهدة"
        verbose_name_plural = "تسويات العهد"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"تسوية {self.custody.custody_number} - {self.date}"


class ExpenseVoucher(models.Model):
    """أذون الصرف"""
    voucher_number = models.CharField("رقم الإذن", max_length=50, unique=True)
    
    VOUCHER_TYPE_CHOICES = [
        ('expense', 'مصروفات'),
        ('advance', 'سلفة'),
        ('refund', 'استرداد'),
        ('salary', 'راتب'),
        ('bonus', 'مكافأة'),
    ]
    voucher_type = models.CharField("نوع الإذن", max_length=20, choices=VOUCHER_TYPE_CHOICES, default='expense')
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('pending', 'قيد الاعتماد'),
        ('approved', 'معتمد'),
        ('paid', 'مصروف'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='draft')
    
    treasury = models.ForeignKey(Treasury, on_delete=models.PROTECT, verbose_name="الخزينة صارفة",
                                 related_name='expense_vouchers')
    
    beneficiary_name = models.CharField("اسم المستفيد", max_length=200)
    beneficiary_id = models.CharField("رقم الهوية", max_length=50, blank=True)
    
    amount = models.DecimalField("المبلغ", max_digits=15, decimal_places=2, 
                                 validators=[MinValueValidator(Decimal('0.01'))])
    
    EXPENSE_CATEGORY_CHOICES = [
        ('electricity', 'كهرباء'),
        ('water', 'مياه'),
        ('gas', 'غاز'),
        ('rent', 'إيجار'),
        ('salaries', 'رواتب'),
        ('maintenance', 'صيانة'),
        ('supplies', 'مستلزمات'),
        ('transport', 'نقل ومواصلات'),
        ('marketing', 'تسويق'),
        ('other', 'أخرى'),
    ]
    expense_category = models.CharField("تصنيف المصروف", max_length=20, choices=EXPENSE_CATEGORY_CHOICES, 
                                        default='other')
    
    cost_center = models.ForeignKey('finance.CostCenter', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="مركز التكلفة")
    
    description = models.TextField("البيان / الغرض")
    
    date = models.DateField("التاريخ", default=timezone.now)
    paid_date = models.DateField("تاريخ الصرف", null=True, blank=True)
    
    # الاعتمادات
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='requested_vouchers',
                                     verbose_name="طالب الصرف")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_vouchers', verbose_name="معتمد بواسطة")
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='paid_vouchers', verbose_name="صرف بواسطة")
    
    attachment = models.FileField("المرفقات", upload_to='vouchers/', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "إذن صرف"
        verbose_name_plural = "الخزينة - أذون الصرف"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.voucher_number} - {self.beneficiary_name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.voucher_number:
            last = ExpenseVoucher.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.voucher_number = f"EXP-{num:05d}"
        super().save(*args, **kwargs)


class ReceiptVoucher(models.Model):
    """أذون القبض"""
    voucher_number = models.CharField("رقم الإذن", max_length=50, unique=True)
    
    VOUCHER_TYPE_CHOICES = [
        ('sales', 'مبيعات'),
        ('collection', 'تحصيل'),
        ('deposit', 'إيداع'),
        ('refund_in', 'استرداد وارد'),
        ('other', 'أخرى'),
    ]
    voucher_type = models.CharField("نوع الإذن", max_length=20, choices=VOUCHER_TYPE_CHOICES, default='collection')
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='draft')
    
    treasury = models.ForeignKey(Treasury, on_delete=models.PROTECT, verbose_name="الخزينة المستلمة",
                                 related_name='receipt_vouchers')
    
    payer_name = models.CharField("اسم الدافع", max_length=200)
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'نقداً'),
        ('check', 'شيك'),
        ('transfer', 'تحويل بنكي'),
        ('card', 'بطاقة'),
    ]
    payment_method = models.CharField("طريقة الدفع", max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    
    cash_amount = models.DecimalField("المبلغ النقدي", max_digits=15, decimal_places=2, default=0)
    gold_weight = models.DecimalField("وزن الذهب", max_digits=15, decimal_places=3, default=0)
    gold_carat = models.ForeignKey('core.Carat', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="العيار")
    
    cost_center = models.ForeignKey('finance.CostCenter', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="مركز التكلفة")
    
    description = models.TextField("البيان")
    date = models.DateField("التاريخ", default=timezone.now)
    
    received_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="استلم بواسطة")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "إذن قبض"
        verbose_name_plural = "الخزينة - أذون القبض"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.voucher_number} - {self.payer_name}"
    
    def save(self, *args, **kwargs):
        if not self.voucher_number:
            last = ReceiptVoucher.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.voucher_number = f"REC-{num:05d}"
        super().save(*args, **kwargs)


class TreasuryTransfer(models.Model):
    """تحويلات بين الخزائن"""
    transfer_number = models.CharField("رقم التحويل", max_length=50, unique=True)
    
    from_treasury = models.ForeignKey(Treasury, on_delete=models.PROTECT, related_name='transfers_out',
                                      verbose_name="من خزينة")
    to_treasury = models.ForeignKey(Treasury, on_delete=models.PROTECT, related_name='transfers_in',
                                    verbose_name="إلى خزينة")
    
    cash_amount = models.DecimalField("المبلغ النقدي", max_digits=15, decimal_places=2, default=0)
    gold_weight = models.DecimalField("وزن الذهب", max_digits=15, decimal_places=3, default=0)
    stones_weight = models.DecimalField("وزن الأحجار", max_digits=15, decimal_places=3, default=0)
    gold_carat = models.ForeignKey('core.Carat', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="العيار")
    
    @property
    def stones_weight_in_gold(self):
        """تحويل وزن الأحجار (قيراط) إلى ما يعادله ذهب (جرام) - التحييف"""
        from decimal import Decimal
        return (self.stones_weight or Decimal('0')) * Decimal('0.2')
    
    @property
    def net_gold_weight(self):
        """صافي الذهب (الوزن - تحييف الأحجار)"""
        return self.gold_weight - self.stones_weight_in_gold
    cost_center = models.ForeignKey('finance.CostCenter', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="مركز التكلفة")
    
    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    notes = models.TextField("ملاحظات", blank=True)
    date = models.DateField("التاريخ", default=timezone.now)
    
    initiated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='initiated_transfers',
                                     verbose_name="بادر بالتحويل")
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='confirmed_transfers', verbose_name="أكد الاستلام")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "تحويل بين خزائن"
        verbose_name_plural = "الخزينة - التحويلات"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.transfer_number}: {self.from_treasury} ← {self.to_treasury}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            last = TreasuryTransfer.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.transfer_number = f"TRF-{num:05d}"
        super().save(*args, **kwargs)


class DailyTreasuryReport(models.Model):
    """تقرير الخزينة اليومي"""
    treasury = models.ForeignKey(Treasury, on_delete=models.CASCADE, related_name='daily_reports',
                                 verbose_name="الخزينة")
    date = models.DateField("التاريخ")
    
    # الأرصدة الافتتاحية
    opening_cash = models.DecimalField("رصيد نقدي افتتاحي", max_digits=15, decimal_places=2, default=0)
    opening_gold_18 = models.DecimalField("رصيد ذهب 18 افتتاحي", max_digits=15, decimal_places=3, default=0)
    opening_gold_21 = models.DecimalField("رصيد ذهب 21 افتتاحي", max_digits=15, decimal_places=3, default=0)
    opening_gold_24 = models.DecimalField("رصيد ذهب 24 افتتاحي", max_digits=15, decimal_places=3, default=0)
    opening_gold_casting = models.DecimalField("رصيد سبك افتتاحي", max_digits=15, decimal_places=3, default=0)
    opening_stones = models.DecimalField("رصيد أحجار افتتاحي", max_digits=15, decimal_places=3, default=0)
    
    # الحركات
    total_cash_in = models.DecimalField("إجمالي الوارد نقداً", max_digits=15, decimal_places=2, default=0)
    total_cash_out = models.DecimalField("إجمالي الصادر نقداً", max_digits=15, decimal_places=2, default=0)
    total_gold_in = models.DecimalField("إجمالي الوارد ذهب", max_digits=15, decimal_places=3, default=0)
    total_gold_out = models.DecimalField("إجمالي الصادر ذهب", max_digits=15, decimal_places=3, default=0)
    
    # الأرصدة الختامية
    closing_cash = models.DecimalField("رصيد نقدي ختامي", max_digits=15, decimal_places=2, default=0)
    closing_gold_18 = models.DecimalField("رصيد ذهب 18 ختامي", max_digits=15, decimal_places=3, default=0)
    closing_gold_21 = models.DecimalField("رصيد ذهب 21 ختامي", max_digits=15, decimal_places=3, default=0)
    closing_gold_24 = models.DecimalField("رصيد ذهب 24 ختامي", max_digits=15, decimal_places=3, default=0)
    closing_gold_casting = models.DecimalField("رصيد سبك ختامي", max_digits=15, decimal_places=3, default=0)
    closing_stones = models.DecimalField("رصيد أحجار ختامي", max_digits=15, decimal_places=3, default=0)
    
    # الجرد الفعلي
    actual_cash = models.DecimalField("النقدية الفعلية", max_digits=15, decimal_places=2, null=True, blank=True)
    actual_gold_18 = models.DecimalField("ذهب 18 فعلي", max_digits=15, decimal_places=3, null=True, blank=True)
    actual_gold_21 = models.DecimalField("ذهب 21 فعلي", max_digits=15, decimal_places=3, null=True, blank=True)
    actual_gold_24 = models.DecimalField("ذهب 24 فعلي", max_digits=15, decimal_places=3, null=True, blank=True)
    actual_gold_casting = models.DecimalField("سبك فعلي", max_digits=15, decimal_places=3, null=True, blank=True)
    actual_stones = models.DecimalField("أحجار فعلي", max_digits=15, decimal_places=3, null=True, blank=True)
    
    # الفروق
    cash_difference = models.DecimalField("فرق نقدي", max_digits=15, decimal_places=2, default=0)
    gold_difference = models.DecimalField("فرق ذهب", max_digits=15, decimal_places=3, default=0)
    gold_casting_difference = models.DecimalField("فرق سبك", max_digits=15, decimal_places=3, default=0)
    stones_difference = models.DecimalField("فرق أحجار", max_digits=15, decimal_places=3, default=0)
    
    notes = models.TextField("ملاحظات", blank=True)
    
    is_closed = models.BooleanField("مغلق", default=False)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="أغلق بواسطة")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "تقرير خزينة يومي"
        verbose_name_plural = "الخزينة - التقارير اليومية"
        unique_together = ('treasury', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.treasury.name} - {self.date}"
    
    def calculate_differences(self):
        """حساب الفروق بين الفعلي والدفتري"""
        if self.actual_cash is not None:
            self.cash_difference = self.actual_cash - self.closing_cash
        if self.actual_gold_18 is not None and self.actual_gold_21 is not None and self.actual_gold_24 is not None:
            actual_total = self.actual_gold_18 + self.actual_gold_21 + self.actual_gold_24
            closing_total = self.closing_gold_18 + self.closing_gold_21 + self.closing_gold_24
            self.gold_difference = actual_total - closing_total
            
        if self.actual_gold_casting is not None:
            self.gold_casting_difference = self.actual_gold_casting - self.closing_gold_casting
            
        if self.actual_stones is not None:
            self.stones_difference = self.actual_stones - self.closing_stones


class TreasuryTool(models.Model):
    """رصيد المواد والمستلزمات في الخزينة"""
    treasury = models.ForeignKey(Treasury, on_delete=models.CASCADE, related_name='tool_balances', verbose_name="الخزينة")
    tool = models.ForeignKey('manufacturing.InstallationTool', on_delete=models.CASCADE, verbose_name="الأداة/المستلزم")
    
    quantity = models.DecimalField("الكمية المتوفرة", max_digits=12, decimal_places=2, default=0)
    weight = models.DecimalField("الوزن المتوفر (جرام)", max_digits=12, decimal_places=3, default=0)
    
    class Meta:
        verbose_name = "رصيد مستلزمات الخزينة"
        verbose_name_plural = "أرصدة مستلزمات الخزائن"
        unique_together = ('treasury', 'tool')

    def __str__(self):
        return f"{self.tool.name} في {self.treasury.name}"


class ToolTransfer(models.Model):
    """تحويل المستلزمات بين الخزائن"""
    transfer_number = models.CharField("رقم التحويل", max_length=50, unique=True)
    from_treasury = models.ForeignKey(Treasury, on_delete=models.CASCADE, related_name='tool_transfers_out', verbose_name="من خزينة")
    to_treasury = models.ForeignKey(Treasury, on_delete=models.CASCADE, related_name='tool_transfers_in', verbose_name="إلى خزينة")
    
    tool = models.ForeignKey('manufacturing.InstallationTool', on_delete=models.CASCADE, verbose_name="الأداة/المستلزم")
    quantity = models.DecimalField("الكمية المحولة", max_digits=12, decimal_places=2, default=0)
    weight = models.DecimalField("الوزن المحول (جرام)", max_digits=12, decimal_places=3, default=0)
    
    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    initiated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='initiated_tool_transfers', verbose_name="بادر بالتحويل")
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_tool_transfers', verbose_name="أكد الاستلام")
    
    date = models.DateField("التاريخ", default=timezone.now)
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "تحويل مستلزمات"
        verbose_name_plural = "تحويلات المستلزمات"

    def __str__(self):
        return f"{self.transfer_number}: {self.tool.name}"

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            last = ToolTransfer.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.transfer_number = f"TTRF-{num:05d}"
        super().save(*args, **kwargs)


class CustodyTool(models.Model):
    """المستلزمات المصروفة عهدة"""
    custody = models.ForeignKey(Custody, on_delete=models.CASCADE, related_name='tools', verbose_name="سند العهدة")
    tool = models.ForeignKey('manufacturing.InstallationTool', on_delete=models.CASCADE, verbose_name="الأداة/المستلزم")
    
    quantity = models.DecimalField("الكمية المصروفة", max_digits=12, decimal_places=2, default=0)
    weight = models.DecimalField("الوزن المصروف (جرام)", max_digits=12, decimal_places=3, default=0)
    
    returned_quantity = models.DecimalField("الكمية المردودة", max_digits=12, decimal_places=2, default=0)
    returned_weight = models.DecimalField("الوزن المردود (جرام)", max_digits=12, decimal_places=3, default=0)

    class Meta:
        verbose_name = "مستلزم عهدة"
        verbose_name_plural = "مستلزمات العهد"

    def __str__(self):
        return f"{self.tool.name} (عهدة {self.custody.custody_number})"
