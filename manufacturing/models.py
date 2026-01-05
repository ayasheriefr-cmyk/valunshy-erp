from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from inventory.models import Carat, Branch, Item, RawMaterial

class Workshop(models.Model):
    """الورش ومصانع التشغيل"""
    name = models.CharField("اسم الورشة", max_length=100)
    contact_person = models.CharField("المسؤول", max_length=100, blank=True)
    
    WORKSHOP_TYPE_CHOICES = [
        ('internal', 'ورشة داخلية (مرتب ثابت)'),
        ('external', 'ورشة خارجية (بالجرام / قطعة)'),
    ]
    workshop_type = models.CharField("نوع الورشة", max_length=20, choices=WORKSHOP_TYPE_CHOICES, default='internal')
    
    phone = models.CharField("رقم الهاتف", max_length=20, blank=True)
    address = models.TextField("العنوان", blank=True)
    
    # Workshop Accounts (Weight-based)
    gold_balance_18 = models.DecimalField("رصيد ذهب 18 (جرام)", max_digits=12, decimal_places=3, default=0)
    gold_balance_21 = models.DecimalField("رصيد ذهب 21 (جرام)", max_digits=12, decimal_places=3, default=0)
    gold_balance_24 = models.DecimalField("رصيد ذهب 24 (جرام)", max_digits=12, decimal_places=3, default=0)
    
    filings_balance_18 = models.DecimalField("رصيد براده 18 (جرام)", max_digits=12, decimal_places=3, default=0)
    filings_balance_21 = models.DecimalField("رصيد براده 21 (جرام)", max_digits=12, decimal_places=3, default=0)
    filings_balance_24 = models.DecimalField("رصيد براده 24 (جرام)", max_digits=12, decimal_places=3, default=0)
    
    # Scrap/Fragments Accounts (الخسية/ككسر)
    scrap_balance_18 = models.DecimalField("رصيد خسية 18 (جرام)", max_digits=12, decimal_places=3, default=0)
    scrap_balance_21 = models.DecimalField("رصيد خسية 21 (جرام)", max_digits=12, decimal_places=3, default=0)
    scrap_balance_24 = models.DecimalField("رصيد خسية 24 (جرام)", max_digits=12, decimal_places=3, default=0)
    
    labor_balance = models.DecimalField("رصيد النقدية (مصنعيات)", max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ورشة فنية"
        verbose_name_plural = "التصنيع - الورش"

    def __str__(self):
        return self.name

class WorkshopSettlement(models.Model):
    """تسويات حسابات الورش (نقدية أو وزن)"""
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='settlements', verbose_name="الورشة")
    date = models.DateField("تاريخ التسوية", auto_now_add=True, db_index=True)
    
    SETTLEMENT_TYPE_CHOICES = [
        ('gold_payment', 'دفع ذهب للورشة'),
        ('labor_payment', 'دفع مصنعيات (نقد)'),
        ('scrap_receive', 'استلام خسية/هالك (واضح)'),
        ('powder_receive', 'استلام بودر/جلي (يحتاج تحليل)'),
    ]
    settlement_type = models.CharField("نوع التسوية", max_length=20, choices=SETTLEMENT_TYPE_CHOICES)
    
    # Amount or Weight
    amount = models.DecimalField("المبلغ النقدي", max_digits=15, decimal_places=2, default=0)
    
    # Weight Details
    weight = models.DecimalField("الوزن الصافي (بعد التحليل)", max_digits=12, decimal_places=3, default=0)
    gross_weight = models.DecimalField("الوزن القائم (قبل التحليل)", max_digits=12, decimal_places=3, default=0, help_text="وزن البودر كما هو")
    
    carat = models.ForeignKey(Carat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="العيار (في حالة الذهب)")
    
    reference = models.CharField("رقم السند/المرجع", max_length=100, blank=True)
    notes = models.TextField("ملاحظات إضافية", blank=True)

    class Meta:
        verbose_name = "تسويه ورشة"
        verbose_name_plural = "التصنيع - تسويات الورش"

    def __str__(self):
        return f"{self.get_settlement_type_display()} - {self.workshop.name}"


class ManufacturingCylinder(models.Model):
    """سلندرات التصنيع/السبك"""
    cylinder_number = models.CharField("رقم السلندر", max_length=50, unique=True)
    name = models.CharField("اسم/وصف السلندر", max_length=200, blank=True)
    image = models.ImageField("صورة السلندر", upload_to='cylinders/', null=True, blank=True)
    
    # المواصفات
    size = models.CharField("المقاس", max_length=50, blank=True)
    capacity = models.DecimalField("السعة (جرام)", max_digits=10, decimal_places=3, default=0)
    material = models.CharField("الخامة", max_length=100, blank=True)
    
    STATUS_CHOICES = [
        ('available', 'متاح'),
        ('in_use', 'قيد الاستخدام'),
        ('maintenance', 'صيانة'),
        ('retired', 'خارج الخدمة'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='available')
    
    # الورشة المسؤولة
    workshop = models.ForeignKey(Workshop, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="الورشة", related_name='cylinders')
    
    # التتبع
    purchase_date = models.DateField("تاريخ الشراء", null=True, blank=True)
    last_maintenance = models.DateField("آخر صيانة", null=True, blank=True)
    notes = models.TextField("ملاحظات", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "سلندر تصنيع"
        verbose_name_plural = "التصنيع - سلندرات السبك"
        ordering = ['cylinder_number']
    
    def __str__(self):
        return f"{self.cylinder_number} - {self.name or 'سلندر'}"

class StoneCategoryGroup(models.Model):
    """مجموعات أصناف الأحجار/الألماس"""
    code = models.IntegerField("الكود", unique=True)
    name = models.CharField("البيان", max_length=100)
    short_code = models.CharField("البيان المختصر", max_length=10)
    commission = models.DecimalField("العمولة", max_digits=10, decimal_places=4, default=0)
    
    class Meta:
        verbose_name = "مجموعة أصناف ألماس"
        verbose_name_plural = "التصنيع - مجموعات أصناف الألماس"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.short_code})"


class StoneCut(models.Model):
    """أشكال/قطع الأحجار"""
    code = models.CharField("كود الصنف", max_length=10, unique=True)
    name = models.CharField("اسم الصنف", max_length=100)
    description = models.TextField("الوصف", blank=True)
    category_group = models.ForeignKey(StoneCategoryGroup, on_delete=models.SET_NULL, 
                                       null=True, blank=True, verbose_name="المجموعة",
                                       related_name='stone_cuts')
    
    class Meta:
        verbose_name = "صنف حجارة"
        verbose_name_plural = "التصنيع - أصناف الحجارة"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class StoneModel(models.Model):
    """موديلات/مقاسات الحجارة"""
    code = models.CharField("كود الموديل", max_length=20, unique=True)
    name = models.CharField("اسم الموديل", max_length=100)
    stone_cut = models.ForeignKey(StoneCut, on_delete=models.CASCADE, 
                                  verbose_name="اسم الصنف", related_name='models')
    
    class Meta:
        verbose_name = "موديل حجارة"
        verbose_name_plural = "التصنيع - موديلات الحجارة"
        ordering = ['stone_cut', 'code']
    
    def __str__(self):
        return f"{self.code} ({self.stone_cut.code})"


class StoneSize(models.Model):
    """مقاسات الحجارة - جدول التسعير والمواصفات"""
    code = models.IntegerField("كود الحجر", unique=True)
    
    # الصنف والموديل
    stone_cut = models.ForeignKey(StoneCut, on_delete=models.CASCADE, 
                                  verbose_name="اسم الصنف", related_name='sizes')
    stone_model = models.ForeignKey(StoneModel, on_delete=models.CASCADE,
                                    verbose_name="اسم الموديل", related_name='sizes')
    
    # نوع الحجر والحرف المختصر
    stone_type = models.CharField("نوع الحجر", max_length=50, blank=True)
    short_code = models.CharField("الحرف المختصر", max_length=20, blank=True)
    
    # نطاق الوزن
    weight_from = models.DecimalField("من وزن", max_digits=10, decimal_places=3, default=0)
    weight_to = models.DecimalField("الى وزن", max_digits=10, decimal_places=3, default=0)
    
    # المقاس بالملم
    size_mm = models.DecimalField("مقاس mm", max_digits=10, decimal_places=3, default=0)
    
    # التسعير
    price_per_carat = models.DecimalField("سعر القراط", max_digits=10, decimal_places=2, default=0)
    
    # اللون والنقاء
    COLOR_CHOICES = [
        ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'),
        ('I', 'I'), ('J', 'J'), ('K', 'K'), ('L', 'L'), ('M', 'M'),
        ('G-H', 'G-H'), ('G H', 'G H'), ('G-I', 'G-I'), ('H-I', 'H-I'),
    ]
    color = models.CharField("اللون", max_length=10, choices=COLOR_CHOICES, default='G-H')
    
    CLARITY_CHOICES = [
        ('IF', 'IF - Internally Flawless'),
        ('VVS', 'VVS - Very Very Slightly Included'),
        ('VVS1', 'VVS1'),
        ('VVS2', 'VVS2'),
        ('VS', 'VS - Very Slightly Included'),
        ('VS1', 'VS1'),
        ('VS2', 'VS2'),
        ('SI', 'SI - Slightly Included'),
        ('SI1', 'SI1'),
        ('SI2', 'SI2'),
        ('I1', 'I1 - Included'),
    ]
    clarity = models.CharField("درجة النقاء", max_length=10, choices=CLARITY_CHOICES, default='VVS')
    
    class Meta:
        verbose_name = "مقاس حجر"
        verbose_name_plural = "التصنيع - مقاسات الحجارة"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.stone_cut.code} - {self.stone_model.name}"


class Stone(models.Model):
    """الأحجار الكريمة والفصوص"""
    name = models.CharField("اسم الحفر/الحجر", max_length=100)
    stone_type = models.CharField("النوع", max_length=50, blank=True)  # Diamond, Zircon, etc.
    stone_cut = models.ForeignKey(StoneCut, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="شكل القطع", related_name='stones')
    stone_size = models.ForeignKey(StoneSize, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="المقاس المحدد", related_name='stones_inventory')
    
    UNIT_CHOICES = [
        ('carat', 'قيراط (Carat)'),
        ('gram', 'جرام (Gram)'),
        ('cm', 'سنتيمتر (CM)'),
    ]
    unit = models.CharField("الوحدة", max_length=20, choices=UNIT_CHOICES, default='carat')
    current_stock = models.DecimalField("الرصيد الحالي (وزن)", max_digits=10, decimal_places=3, default=0)
    current_quantity = models.PositiveIntegerField("العدد الحالي (قطعة)", default=0)

    class Meta:
        verbose_name = "حجر كريم / فص"
        verbose_name_plural = "التصنيع - مخزن الفصوص"

    def __str__(self):
        cut_info = f"{self.stone_cut.name} " if self.stone_cut else ""
        size_info = f" - {self.stone_size.size_mm}mm" if self.stone_size else ""
        return f"{cut_info}{self.name}{size_info} ({self.current_stock} {self.unit} / {self.current_quantity} قطعة)"

class StoneInventoryAudit(models.Model):
    """نظام جرد الأحجار"""
    audit_date = models.DateField("تاريخ الجرد", default=timezone.now)
    stone = models.ForeignKey(Stone, on_delete=models.CASCADE, verbose_name="الحجر", related_name='audits')
    
    system_stock = models.DecimalField("الرصيد الدفتري (وزن)", max_digits=10, decimal_places=3)
    physical_stock = models.DecimalField("الرصيد الفعلي (وزن)", max_digits=10, decimal_places=3)
    difference = models.DecimalField("الفرق (وزن)", max_digits=10, decimal_places=3, editable=False)
    
    system_quantity = models.PositiveIntegerField("العدد الدفتري", default=0)
    physical_quantity = models.PositiveIntegerField("العدد الفعلي", default=0)
    difference_quantity = models.IntegerField("الفرق (عدد)", editable=False, default=0)
    
    notes = models.TextField("ملاحظات الجرد", blank=True)
    audited_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, verbose_name="بواسطة")

    def save(self, *args, **kwargs):
        self.difference = self.physical_stock - self.system_stock
        self.difference_quantity = int(self.physical_quantity) - int(self.system_quantity)
        super().save(*args, **kwargs)
        
        # Optionally update stone stock upon audit confirmation
        # self.stone.current_stock = self.physical_stock
        # self.stone.save()

    class Meta:
        verbose_name = "جرد أحجار"
        verbose_name_plural = "التصنيع - جرد الأحجار"
        ordering = ['-audit_date']

class InstallationTool(models.Model):
    """أدوات ومستلزمات التركيب"""
    name = models.CharField("اسم الأداة/المستلزم", max_length=100)
    description = models.TextField("الوصف/المواصفات", blank=True)
    
    # For quantity-based tools
    quantity = models.IntegerField("العدد المتوفر", default=0)
    min_quantity = models.IntegerField("حد الطلب", default=1)
    
    # For weight-based tools (gold tools)
    weight = models.DecimalField("الوزن (جرام)", max_digits=10, decimal_places=3, default=0)
    min_weight = models.DecimalField("حد الوزن الأدنى", max_digits=10, decimal_places=3, default=0)
    
    UNIT_CHOICES = [
        ('piece', 'قطعة'),
        ('gram', 'جرام'),
        ('meter', 'متر'),
        ('roll', 'لفة'),
    ]
    unit = models.CharField("وحدة القياس", max_length=10, choices=UNIT_CHOICES, default='piece')
    
    TOOL_TYPE_CHOICES = [
        ('consumable', 'مستهلكات (شمع/جبس/..)'),
        ('equipment', 'عدد وأدوات (مبارد/زراديات/..)'),
        ('spare_part', 'قطع غيار ماكينات'),
        ('gold_wire', 'سلك ذهب (ليزر/لحام)'),
        ('gold_solder', 'لحام ذهب'),
        ('cadmium', 'كيديم'),
        ('gold_sheet', 'رقائق ذهب'),
    ]
    tool_type = models.CharField("نوع الأداة", max_length=20, choices=TOOL_TYPE_CHOICES, default='consumable')
    
    # Carat for gold-based tools
    carat = models.ForeignKey('core.Carat', on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name="العيار", help_text="للأدوات الذهبية فقط")

    class Meta:
        verbose_name = "أداة تركيب / مستلزمات"
        verbose_name_plural = "التصنيع - مخزن أدوات التركيب"

    def __str__(self):
        if self.unit == 'gram':
            return f"{self.name} ({self.weight} جم)"
        return f"{self.name} ({self.quantity})"
    
    @property
    def is_gold_tool(self):
        return self.tool_type in ['gold_wire', 'gold_solder', 'cadmium', 'gold_sheet']

class ManufacturingOrder(models.Model):
    order_number = models.CharField("رقم الأمر", max_length=50, unique=True)
    workshop = models.ForeignKey(Workshop, on_delete=models.SET_NULL, null=True, verbose_name="الورشة", related_name='orders')
    carat = models.ForeignKey(Carat, on_delete=models.PROTECT, verbose_name="العيار")
    resulting_item = models.OneToOneField(Item, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="القطعة الناتجة في المخزن", related_name='source_order')
    
    # Gold movements
    input_material = models.ForeignKey(RawMaterial, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المادة الخام المصروفة")
    input_weight = models.DecimalField("وزن الذهب الداخل", max_digits=12, decimal_places=3)
    output_weight = models.DecimalField("وزن القطع الناتجة", max_digits=12, decimal_places=3, default=0)
    scrap_weight = models.DecimalField(
        "وزن الهالك/الخسية", 
        max_digits=12, 
        decimal_places=3, 
        default=0,
        help_text="المعيار المعتمد: 0.5% - 1.0%"
    )
    powder_weight = models.DecimalField("وزن البودر (المسترد)", max_digits=12, decimal_places=3, default=0)
    
    # Stones tracking
    stones = models.ManyToManyField(Stone, through='OrderStone', verbose_name="الفصوص المستخدمة")
    total_stone_weight = models.DecimalField("إجمالي وزن الفصوص (جم)", max_digits=10, decimal_places=3, default=0)
    
    # Tools tracking
    tools = models.ManyToManyField(InstallationTool, through='OrderTool', verbose_name="المستلزمات والأدوات المستخدمة")
    
    # Financials
    labor_rate = models.DecimalField("أجر الجرام (للورش الخارجية)", max_digits=10, decimal_places=2, default=0, help_text="اتركه 0 للورش الداخلية (نظام المرتبات)")
    manufacturing_pay = models.DecimalField("إجمالي الأجر المستحق", max_digits=12, decimal_places=2, default=0, help_text="المبلغ الذي سيتم إضافته لرصيد الورشة. اتركه 0 للورش الداخلية.")
    factory_margin = models.DecimalField("هامش ربح المصنع", max_digits=12, decimal_places=2, default=0)
    
    # Factory Overhead Costs (Distributed)
    cost_allocation = models.ForeignKey('CostAllocation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="فترة التكاليف")
    
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
    def total_making_cost(self):
        """إجمالي تكلفة المصنعية (أجور + تكاليف + هامش)"""
        return self.manufacturing_pay + self.total_overhead + self.factory_margin

    # Auto-Inventory Creation Fields
    auto_create_item = models.BooleanField("إنشاء قطعة في المخزن تلقائياً عند الاكتمال", default=True)
    item_name_pattern = models.CharField("اسم الصنف الناتج", max_length=255, blank=True, help_text="مثال: خاتم ذهب عيار 21")
    target_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الفرع المستلم")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status
        self._original_input_weight = self.input_weight

    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('in_progress', 'تحت التشغيل'),
        ('casting', 'سبك'),
        ('crafting', 'صياغة'),
        ('polishing', 'تلميع / واجهة'),
        ('tribolish', 'الترابولش'),
        ('merged', 'مدمج مع أمر آخر'),
        ('qc_pending', 'قيد فحص الجودة'),
        ('completed', 'مكتمل / جاهز'),
        ('qc_failed', 'فحص جودة مرفوض'),
        ('cancelled', 'ملغى'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # QC Fields
    qc_technician = models.CharField("الفني الفاحص", max_length=255, blank=True)
    qc_notes = models.TextField("ملاحظات الجودة", blank=True)
    final_product_image = models.ImageField("صورة المنتج النهائي", upload_to='products/final/', null=True, blank=True)
    
    assigned_technician = models.CharField("الفني المسؤول", max_length=255, blank=True)
    
    start_date = models.DateField("تاريخ البدء", auto_now_add=True, db_index=True)
    end_date = models.DateField("تاريخ الانتهاء", null=True, blank=True)

    def get_total_tools_weight(self):
        """Calculates the total weight of gold-based tools/materials added to the order."""
        from django.db.models import Sum
        gold_types = ['gold_wire', 'gold_solder', 'cadmium', 'gold_sheet']
        return self.order_tools_list.filter(tool__tool_type__in=gold_types).aggregate(total=Sum('weight'))['total'] or 0

    def __str__(self):
        return self.order_number

    class Meta:
        verbose_name = "أمر تصنيع"
        verbose_name_plural = "التصنيع - أوامر العمل"

class OrderStone(models.Model):
    order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE)
    stone = models.ForeignKey(Stone, on_delete=models.CASCADE, verbose_name="الحجر")
    
    # Link to Production Stage (usually mounting stage)
    production_stage = models.ForeignKey('ProductionStage', on_delete=models.SET_NULL, null=True, blank=True, 
                                        verbose_name="مرحلة الصرف (التركيب)", 
                                        help_text="المرحلة التي تم فيها صرف الأحجار")
    
    # Stone Quantity Tracking
    quantity_required = models.DecimalField("الكمية المطلوبة (في المنتج)", max_digits=10, decimal_places=3, default=0)
    quantity_issued = models.DecimalField("الكمية المصروفة الفعلية", max_digits=10, decimal_places=3, default=0)
    
    # Legacy field for backward compatibility (will be auto-calculated)
    quantity = models.DecimalField("إجمالي المصروف", max_digits=10, decimal_places=3, editable=False)
    
    @property
    def quantity_broken(self):
        """الأحجار المكسورة/المفقودة"""
        return max(0, self.quantity_issued - self.quantity_required)
    
    def save(self, *args, **kwargs):
        # Auto-calculate total quantity
        self.quantity = self.quantity_issued
        super().save(*args, **kwargs)
    
    @property
    def weight_in_gold(self):
        """تحويل وزن الأحجار (قيراط) إلى ما يعادله ذهب (جرام) - التحييف"""
        from decimal import Decimal
        
        if not self.stone:
            return Decimal('0')
            
        # Normalize unit string
        unit = str(self.stone.unit).lower().strip()
        qty = self.quantity or Decimal('0')
        
        # 1. Grams (Direct Weight)
        if unit in ['gram', 'g', 'gm', 'جرام']:
            return qty
            
        # 2. Carats (Convert to Grams: 1 ct = 0.2 g)
        # Handle 'carat', 'ct', and the Arabic 'قيراط' which caused the issue
        if unit in ['carat', 'ct'] or 'قيراط' in unit:
             return qty * Decimal('0.2')
             
        # 3. Others (CM, etc.) -> 0 weight contribution
        return Decimal('0')
    
    class Meta:
        verbose_name = "فص في أمر"
        verbose_name_plural = "فصوص الأوامر"

class OrderTool(models.Model):
    order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='order_tools_list')
    tool = models.ForeignKey(InstallationTool, on_delete=models.CASCADE, verbose_name="الأداة/المستلزم")
    quantity = models.DecimalField("الكمية المصروفة", max_digits=10, decimal_places=3, default=0, help_text="عند الاستخدام بالعدد")
    weight = models.DecimalField("الوزن المصروف (جم)", max_digits=10, decimal_places=3, default=0, help_text="عند الاستخدام بالجرام")

    class Meta:
        verbose_name = "مستلزم في أمر"
        verbose_name_plural = "مستلزمات الأوامر"

    def __str__(self):
        return f"{self.tool.name} in {self.order.order_number}"

class ProductionStage(models.Model):
    order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='stages')
    STAGE_CHOICES = [
        ('tazgah_qasem', 'تزجة قاسم (تجميع)'),
        ('laser', 'ليزر (لحام/زيادة)'),
        ('mounting_pablo', 'تركيب بابلو'),
        ('polishing', 'الجلي والتلميع'),
        ('mounting_manmouk', 'تركيب منموى (نهائي)'),
        ('design', 'تصميم / 3D Design'),
        ('printing', 'طباعة الشمع / 3D Printing'),
        ('wax_injection', 'حقن الشمع / Wax Injection'),
        ('wax_setting', 'تركيب الشمع / Wax Setting'),
        ('casting', 'السبك / Casting'),
        ('filing', 'البرد والتجهيز / Filing'),
        ('mounting', 'التركيب / Mounting'),
        ('setting', 'تركيب الأحجار / Stone Setting'),
        ('plating', 'الطلاء / Plating'),
        ('enamel', 'المينا / Enamel'),
        ('chains', 'السلاسل / Chains'),
        ('stamping', 'الدمغة / Stamping'),
        ('repair', 'الصيانة / Repairs'),
        ('qc', 'مراقبة الجودة / Quality Control'),
        ('tribolish', 'الترابولش (Tribolish)'),
    ]
    stage_name = models.CharField("اسم المرحلة", max_length=20, choices=STAGE_CHOICES, default='tazgah_qasem')
    
    # Worker/Workshop executing this stage
    workshop = models.ForeignKey(Workshop, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="الورشة/الصنايعي المنفذ")
    
    # Weights
    input_weight = models.DecimalField("الوزن الدخول", max_digits=12, decimal_places=3)
    output_weight = models.DecimalField("الوزن الخروج", max_digits=12, decimal_places=3, default=0)
    
    # Loss/Scrap Details
    powder_weight = models.DecimalField("وزن البودر (براده)", max_digits=10, decimal_places=3, default=0)
    loss_weight = models.DecimalField("وزن الخسية (هالك)", max_digits=10, decimal_places=3, default=0, help_text="الفرق المتبقي")
    
    technician = models.CharField("اسم الفني (نص)", max_length=255, blank=True)
    cylinder = models.ForeignKey(ManufacturingCylinder, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="السلندر المستخدم", help_text="لمرحلة السبك فقط")
    image = models.ImageField("صورة المرحلة", upload_to='production_stages/', null=True, blank=True)
    notes = models.TextField("ملاحظات", blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Time Tracking
    start_datetime = models.DateTimeField("وقت بدء (استلام)", null=True, blank=True)
    end_datetime = models.DateTimeField("وقت تسليم (خروج)", null=True, blank=True)
    
    # Workflow Automations
    next_workshop = models.ForeignKey(Workshop, on_delete=models.SET_NULL, null=True, blank=True, related_name='next_stages', verbose_name="تحويل إلى الورشة التالية")
    is_transferred = models.BooleanField("تم التحويل تلقائياً", default=False)

    @property
    def duration(self):
        if self.start_datetime and self.end_datetime:
            return self.end_datetime - self.start_datetime
        return None

    def __str__(self):
        ws = self.workshop.name if self.workshop else "غير محدد"
        return f"{self.get_stage_name_display()} ({ws})"


class WorkshopTransfer(models.Model):
    transfer_number = models.CharField("رقم التحويل", max_length=50, unique=True)
    from_workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='transfers_out', verbose_name="من ورشة")
    to_workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='transfers_in', verbose_name="إلى ورشة")
    
    carat = models.ForeignKey(Carat, on_delete=models.PROTECT, verbose_name="العيار")
    weight = models.DecimalField("الوزن المحول", max_digits=12, decimal_places=3)
    
    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    initiated_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='initiated_workshop_transfers', verbose_name="بادر بالتحويل")
    confirmed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_workshop_transfers', verbose_name="أكد الاستلام")
    
    date = models.DateField("التاريخ", auto_now_add=True)
    notes = models.TextField("ملاحظات", blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    class Meta:
        verbose_name = "تحويل بين الورش"
        verbose_name_plural = "التصنيع - تحويلات الورش"

    def __str__(self):
        return f"{self.transfer_number} ({self.weight} جم)"

class CostAllocation(models.Model):
    """توزيع تكاليف المصنع (كهرباء، مياه، إيجار...) على أوامر التصنيع"""
    period_name = models.CharField("اسم العهدة/الفترة", max_length=100, help_text="مثال: تكاليف شهر يناير 2026")
    start_date = models.DateField("من تاريخ")
    end_date = models.DateField("إلى تاريخ")
    
    # Overhead Totals (Costs to be distributed)
    total_electricity = models.DecimalField("إجمالي الكهرباء", max_digits=12, decimal_places=2, default=0)
    total_water = models.DecimalField("إجمالي المياه", max_digits=12, decimal_places=2, default=0)
    total_gas = models.DecimalField("إجمالي الغاز", max_digits=12, decimal_places=2, default=0)
    total_rent = models.DecimalField("إجمالي الإيجار", max_digits=12, decimal_places=2, default=0)
    total_salaries = models.DecimalField("إجمالي رواتب إدارية", max_digits=12, decimal_places=2, default=0)
    total_other = models.DecimalField("مصروفات أخرى", max_digits=12, decimal_places=2, default=0)
    
    ALLOCATION_BASIS_CHOICES = [
        ('weight', 'حسب وزن الذهب المنتج (Output Weight)'),
        ('labor', 'حسب أجر التصنيع (Labor Cost)'),
    ]
    allocation_basis = models.CharField("أساس التوزيع", max_length=20, choices=ALLOCATION_BASIS_CHOICES, default='weight')
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('applied', 'تم الترحيل (مغلق)'),
    ]
    status = models.CharField("الحالة", max_length=20, choices=STATUS_CHOICES, default='draft')
    
    cost_center = models.ForeignKey('finance.CostCenter', on_delete=models.SET_NULL, null=True, blank=True, 
                                    verbose_name="مركز التكلفة", help_text="إذا تم الاختيار، سيتم جلب المصاريف الخاصة بهذا المركز فقط (مثل: المصنع)")
    
    
    # Statistics
    total_production_weight_snapshot = models.DecimalField("إجمالي الوزن المنتج في الفترة", max_digits=15, decimal_places=3, default=0, editable=False)
    total_labor_cost_snapshot = models.DecimalField("إجمالي أجور الورش (الخارجية)", max_digits=15, decimal_places=2, default=0, editable=False)
    total_labor_income_snapshot = models.DecimalField("إجمالي الدخل من أجور التصنيع (شامل الهامش)", max_digits=15, decimal_places=2, default=0, editable=False)
    net_labor_profit_snapshot = models.DecimalField("صافي ربح قطاع التصنيع (بعد الأجور والمصاريف)", max_digits=15, decimal_places=2, default=0, editable=False)
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "توزيع تكاليف المصنع"
        verbose_name_plural = "التصنيع - تكاليف المصنع"
        ordering = ['-start_date']

    def __str__(self):
        return self.period_name

    @property
    def total_overhead_amount(self):
        return (self.total_electricity + self.total_water + self.total_gas + 
                self.total_rent + self.total_salaries + self.total_other)

    def fetch_expenses(self):
        """جلب مبالغ المصاريف تلقائياً من أذون الصرف في المالية"""
        from finance.treasury_models import ExpenseVoucher
        from django.db.models import Sum
        from decimal import Decimal
        
        # Filter for paid vouchers in the period
        query = {
            'date__gte': self.start_date,
            'date__lte': self.end_date,
            'status': 'paid'
        }
        if self.cost_center:
            query['cost_center'] = self.cost_center
            
        vouchers = ExpenseVoucher.objects.filter(**query)
    
        
        # Mapping categories to model fields
        mapping = {
            'electricity': 'total_electricity',
            'water': 'total_water',
            'gas': 'total_gas',
            'rent': 'total_rent',
            'salaries': 'total_salaries',
            'other': 'total_other', # Note: mapping 'other' specifically
        }
        
        updated_fields = []
        for cat, field in mapping.items():
            total = vouchers.filter(expense_category=cat).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            if getattr(self, field) != total:
                setattr(self, field, total)
                updated_fields.append(field)
                
        # Also include 'transport', 'maintenance', 'supplies', 'marketing' into 'other' if not handled
        remaining_cats = ['maintenance', 'supplies', 'transport', 'marketing']
        extra_total = vouchers.filter(expense_category__in=remaining_cats).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if extra_total > 0:
            self.total_other += extra_total
            if 'total_other' not in updated_fields:
                updated_fields.append('total_other')
                
        if updated_fields:
            self.save(update_fields=updated_fields)
            return len(updated_fields)
        return 0
    

