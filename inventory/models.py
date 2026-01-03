from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Carat, Branch

class Category(models.Model):
    name = models.CharField(_("Category Name"), max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"

    def __str__(self):
        return self.name

class Item(models.Model):
    barcode = models.CharField("الباركود", max_length=100, unique=True, db_index=True)
    name = models.CharField("اسم الصنف", max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items', verbose_name="التصنيف")
    carat = models.ForeignKey(Carat, on_delete=models.PROTECT, related_name='items', verbose_name="العيار")
    
    # Weights
    gross_weight = models.DecimalField("الوزن القائم", max_digits=10, decimal_places=3)
    stone_weight = models.DecimalField("وزن الأحجار", max_digits=10, decimal_places=3, default=0)
    net_gold_weight = models.DecimalField("صافي الذهب", max_digits=10, decimal_places=3)
    
    # Financials
    labor_fee_per_gram = models.DecimalField("المصنعية/جرام", max_digits=10, decimal_places=2, default=0)
    fixed_labor_fee = models.DecimalField("مصنعية ثابتة (أجور + ربح مصنع)", max_digits=10, decimal_places=2, default=0)
    default_stone_fee = models.DecimalField("قيمة الأحجار الافتراضية", max_digits=10, decimal_places=2, default=0)
    
    # Factory Overhead Cost Breakdown (Synced from Manufacturing Order)
    overhead_electricity = models.DecimalField("نصيب الكهرباء", max_digits=10, decimal_places=2, default=0)
    overhead_water = models.DecimalField("نصيب المياه", max_digits=10, decimal_places=2, default=0)
    overhead_gas = models.DecimalField("نصيب الغاز", max_digits=10, decimal_places=2, default=0)
    overhead_rent = models.DecimalField("نصيب الإيجار", max_digits=10, decimal_places=2, default=0)
    overhead_salaries = models.DecimalField("نصيب الرواتب", max_digits=10, decimal_places=2, default=0)
    overhead_other = models.DecimalField("نصيب مصاريف أخرى", max_digits=10, decimal_places=2, default=0)
    
    @property
    def total_overhead(self):
        """إجمالي التكاليف الصناعية المحملة"""
        return (self.overhead_electricity + self.overhead_water + self.overhead_gas +
                self.overhead_rent + self.overhead_salaries + self.overhead_other)

    @property
    def total_manufacturing_cost(self):
        """إجمالي تكلفة المصنعية (أجور + تكاليف)"""
        return self.fixed_labor_fee + self.total_overhead

    retail_margin = models.DecimalField("هامش ربح التجزئة", max_digits=10, decimal_places=2, default=0)
    
    
    # Tracking
    rfid_tag = models.CharField("كود RFID", max_length=255, blank=True, null=True, unique=True)
    image = models.ImageField("صورة القطعة", upload_to='items/', blank=True, null=True)
    
    status_choices = [
        ('available', _('Available')),
        ('sold', _('Sold')),
        ('manufacturing', _('In Manufacturing')),
        ('mandoob', _('With Delegate')),
        ('reserved', _('Mahjouz (Reserved)')),
        ('lost', _('Lost')),
    ]
    status = models.CharField("الحالة", max_length=20, choices=status_choices, default='available')
    current_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='items', verbose_name="الفرع الحالي")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.barcode} - {self.name}"

    @property
    def stone_weight_in_gold(self):
        """تحويل وزن الأحجار (قيراط) إلى ما يعادله ذهب (جرام) - التحييف"""
        from decimal import Decimal
        return (self.stone_weight or Decimal('0')) * Decimal('0.2')

    def save(self, *args, **kwargs):
        """تطبيق منطق التحييف تلقائياً (صافي الذهب = القائم - تحييف الأحجار)"""
        from decimal import Decimal
        if self.gross_weight is not None:
             # Ensure we subtract decimal from decimal
             gross = Decimal(str(self.gross_weight))
             self.net_gold_weight = gross - self.stone_weight_in_gold
        super().save(*args, **kwargs)

    def calculate_total_cost(self, gold_price_per_gram):
        """حساب التكلفة الكلية تشمل مصاريف تشغيل المصنع الموزعة"""
        return (self.net_gold_weight * gold_price_per_gram) + (self.gross_weight * self.labor_fee_per_gram) + self.fixed_labor_fee + self.total_overhead
    

    class Meta:
        verbose_name = "قطعة ذهب"
        verbose_name_plural = "المخزون - القطع"

class RawMaterial(models.Model):
    name = models.CharField("اسم المادة", max_length=100)
    material_type_choices = [
        ('gold_bar', 'سبائك ذهب'),
        ('gold_grain', 'حبيبات ذهب'),
        ('stones', 'أحجار كريمة'),
        ('scrap', 'ذهب كسر'),
    ]
    material_type = models.CharField("نوع المادة", max_length=20, choices=material_type_choices)
    carat = models.ForeignKey(Carat, on_delete=models.PROTECT, null=True, blank=True, verbose_name="العيار")
    current_weight = models.DecimalField("الوزن الحالي", max_digits=12, decimal_places=3)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="الفرع")

    class Meta:
        verbose_name = "مادة خام"
        verbose_name_plural = "المخزون - المواد الخام"

    def __str__(self):
        return f"{self.name} ({self.get_material_type_display()})"

class ItemTransfer(models.Model):
    """تحويل القطع الجاهزة بين الفروع"""
    transfer_number = models.CharField("رقم التحويل", max_length=50, unique=True)
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='item_transfers_out', verbose_name="من فرع")
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='item_transfers_in', verbose_name="إلى فرع/قسم")
    items = models.ManyToManyField(Item, related_name='transfers', verbose_name="القطع")
    
    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    initiated_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='initiated_item_transfers', verbose_name="بادر بالتحويل")
    confirmed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_item_transfers', verbose_name="أكد الاستلام")
    
    date = models.DateField("التاريخ", auto_now_add=True)
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "تحويل قطع"
        verbose_name_plural = "المخزون - تحويلات القطع"

    def __str__(self):
        return self.transfer_number

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            import datetime
            last = ItemTransfer.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.transfer_number = f"ITRF-{datetime.datetime.now().year}-{num:04d}"
        super().save(*args, **kwargs)

class MaterialTransfer(models.Model):
    """تحويل المواد الخام بين الفروع"""
    transfer_number = models.CharField("رقم التحويل", max_length=50, unique=True)
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='material_transfers_out', verbose_name="من فرع")
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='material_transfers_in', verbose_name="إلى فرع/قسم")
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, verbose_name="المادة الخام")
    weight = models.DecimalField("الوزن المحول", max_digits=12, decimal_places=3)
    
    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    initiated_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='initiated_material_transfers', verbose_name="بادر بالتحويل")
    confirmed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_material_transfers', verbose_name="أكد الاستلام")
    
    date = models.DateField("التاريخ", auto_now_add=True)
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "تحويل مواد خام"
        verbose_name_plural = "المخزون - تحويلات المواد الخام"

    def __str__(self):
        return self.transfer_number

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            import datetime
            last = MaterialTransfer.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.transfer_number = f"MTRF-{datetime.datetime.now().year}-{num:04d}"
        super().save(*args, **kwargs)
