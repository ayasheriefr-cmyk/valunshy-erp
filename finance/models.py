from django.db import models
from django.utils.translation import gettext_lazy as _

class Account(models.Model):
    code = models.CharField("كود الحساب", max_length=20, unique=True)
    name = models.CharField("اسم الحساب", max_length=100)
    
    ACCOUNT_TYPE_CHOICES = [
        ('asset', 'أصول'),
        ('liability', 'خصوم'),
        ('equity', 'حقوق ملكية'),
        ('revenue', 'إيرادات'),
        ('expense', 'مصروفات'),
    ]
    account_type = models.CharField("نوع الحساب", max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name="الحساب الأب")
    
    balance = models.DecimalField("الرصيد النقدي", max_digits=15, decimal_places=2, default=0)
    # Special: Gold Balance (for weight-based accounting)
    gold_balance = models.DecimalField("رصيد الذهب (جرام)", max_digits=15, decimal_places=3, default=0)

    class Meta:
        verbose_name = "حساب مالي"
        verbose_name_plural = "الحسابات - شجرة الحسابات"

    def __str__(self):
        return f"{self.code} - {self.name}"

class JournalEntry(models.Model):
    reference = models.CharField("رقم المرجع", max_length=100) # e.g., Invoice #INV-1001
    description = models.TextField("الوصف / البيان")
    date = models.DateField("تاريخ القيد", default=models.functions.Now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "قيد يومية"
        verbose_name_plural = "الحسابات - قيود اليومية"

    def __str__(self):
        return f"{self.reference} بتاريخ {self.date}"

class CostCenter(models.Model):
    """مراكز التكلفة"""
    code = models.CharField("كود المركز", max_length=20, unique=True)
    name = models.CharField("اسم مركز التكلفة", max_length=100)
    description = models.TextField("وصف المركز", blank=True)
    is_active = models.BooleanField("نشط", default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مركز تكلفة"
        verbose_name_plural = "الحسابات - مراكز التكلفة"

    def __str__(self):
        return f"{self.code} - {self.name}"

class LedgerEntry(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='ledger_entries', verbose_name="قيد اليومية")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="الحساب")
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مركز التكلفة")
    
    debit = models.DecimalField("مدين (نقد)", max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField("دائن (نقد)", max_digits=15, decimal_places=2, default=0)
    
    # Gold Weight tracking in accounting
    gold_debit = models.DecimalField("مدين (ذهب)", max_digits=15, decimal_places=3, default=0)
    gold_credit = models.DecimalField("دائن (ذهب)", max_digits=15, decimal_places=3, default=0)

    class Meta:
        verbose_name = "بند القيد"
        verbose_name_plural = "بنود القيود"

    def __str__(self):
        return f"{self.account.name} | D: {self.debit} C: {self.credit}"

class FinanceSettings(models.Model):
    """ Singleton model to store default accounting mappings """
    cash_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_cash', verbose_name="حساب النقدية")
    sales_revenue_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_revenue', verbose_name="حساب إيرادات المبيعات")
    inventory_gold_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_inventory', verbose_name="حساب مخزون الذهب")
    cost_of_gold_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_cog', verbose_name="حساب تكلفة الذهب")
    vat_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='default_vat', verbose_name="حساب ضريبة القيمة المضافة")
    sales_treasury = models.ForeignKey('finance.Treasury', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_sales', verbose_name="خزينة المبيعات الافتراضية")

    class Meta:
        verbose_name = "إعدادات الحسابات"
        verbose_name_plural = "إعدادات الحسابات"

    def save(self, *args, **kwargs):
        self.pk = 1 # Ensure only one record exists
        super().save(*args, **kwargs)


class FiscalYear(models.Model):
    """السنة المالية"""
    name = models.CharField("اسم السنة", max_length=50, unique=True)  # Added unique
    start_date = models.DateField("تاريخ البداية")
    end_date = models.DateField("تاريخ النهاية")
    is_active = models.BooleanField("السنة الحالية", default=False)
    is_closed = models.BooleanField("مغلقة", default=False)
    
    class Meta:
        verbose_name = "سنة مالية"
        verbose_name_plural = "الحسابات - السنوات المالية"
    
    def __str__(self):
        return self.name
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean() # Ensure validation runs
        # Only one active year at a time
        if self.is_active:
            FiscalYear.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class OpeningBalance(models.Model):
    """الأرصدة الافتتاحية"""
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, verbose_name="السنة المالية")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="الحساب")
    
    debit_balance = models.DecimalField("رصيد مدين", max_digits=15, decimal_places=2, default=0)
    credit_balance = models.DecimalField("رصيد دائن", max_digits=15, decimal_places=2, default=0)
    gold_balance = models.DecimalField("رصيد الذهب (جرام)", max_digits=15, decimal_places=3, default=0)
    
    notes = models.TextField("ملاحظات", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "رصيد افتتاحي"
        verbose_name_plural = "الحسابات - الأرصدة الافتتاحية"
        unique_together = ('fiscal_year', 'account')
    
    def __str__(self):
        return f"{self.account.name} - {self.fiscal_year.name}"


class Partner(models.Model):
    """الشركاء وتوزيع النسب"""
    name = models.CharField("اسم الشريك", max_length=100)
    percentage = models.DecimalField("نسبة الشراكة %", max_digits=5, decimal_places=2, help_text="النسبة المئوية من 100")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="حساب جاري الشريك")
    
    is_active = models.BooleanField("نشط", default=True)
    joined_date = models.DateField("تاريخ الانضمام", auto_now_add=True)

    class Meta:
        verbose_name = "شريك"
        verbose_name_plural = "الشركاء"

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


