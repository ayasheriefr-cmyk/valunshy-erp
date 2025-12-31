from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import ManufacturingOrder, ProductionStage, Workshop, Stone, OrderStone, OrderTool, WorkshopSettlement, InstallationTool, StoneCut, StoneModel, StoneSize, StoneCategoryGroup, ManufacturingCylinder, WorkshopTransfer
from core.admin_mixins import ExportImportMixin

class ProductionStageInline(admin.TabularInline):
    model = ProductionStage
    extra = 1
    fields = (
        'stage_name', 'workshop', 
        'input_weight', 'output_weight', 
        'powder_weight', 'loss_weight',
        'start_datetime', 'end_datetime',
        'next_workshop', 'is_transferred', 'notes'
    )
    # Make timestamps and automation flags READ ONLY to show they are automatic
    readonly_fields = ('timestamp', 'is_transferred', 'loss_weight', 'start_datetime', 'end_datetime')
    autocomplete_fields = ['cylinder']
    classes = ('tabular',) # Ensure standard Django class for popups

class OrderStoneInline(admin.TabularInline):
    model = OrderStone
    extra = 1
    fields = ('stone', 'production_stage', 'quantity_required', 'quantity_issued', 'quantity_broken_display')
    readonly_fields = ('quantity_broken_display',)
    verbose_name = "فص مصروف للأمر"
    verbose_name_plural = "الأحجار والفصوص المستخدمة"
    
    def quantity_broken_display(self, obj):
        if obj.pk:
            broken = obj.quantity_broken
            if broken > 0:
                return format_html('<span style="color:#f44336; font-weight:bold;">⚠️ {} كسر</span>', broken)
            return format_html('<span style="color:#4CAF50;">✓ لا يوجد</span>')
        return '-'
    quantity_broken_display.short_description = 'الكسر/الفقد'

class OrderToolInline(admin.TabularInline):
    model = OrderTool
    extra = 1
    verbose_name = "مستلزم مصروف للأمر"
    verbose_name_plural = "الأدوات والمستلزمات المستخدمة"


@admin.register(ManufacturingCylinder)
class ManufacturingCylinderAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('cylinder_number', 'name', 'cylinder_image', 'size', 'capacity', 'status_badge', 'workshop')
    list_filter = ('status', 'workshop')
    search_fields = ('cylinder_number', 'name')
    ordering = ('cylinder_number',)
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('cylinder_number', 'name'), 'image', 'status')
        }),
        ('المواصفات', {
            'fields': (('size', 'capacity'), 'material', 'workshop')
        }),
        ('التتبع', {
            'fields': (('purchase_date', 'last_maintenance'), 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def cylinder_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:50px; height:50px; object-fit:cover; border-radius:5px;"/>', obj.image.url)
        return mark_safe('<span style="color:#999;">لا توجد صورة</span>')
    cylinder_image.short_description = 'الصورة'
    
    def status_badge(self, obj):
        colors = {
            'available': '#4CAF50',
            'in_use': '#2196F3',
            'maintenance': '#FF9800',
            'retired': '#f44336',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; font-weight:bold;">{}</span>',
            color, color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'


@admin.register(StoneCategoryGroup)
class StoneCategoryGroupAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'short_code', 'commission', 'cuts_count')
    search_fields = ('name', 'short_code')
    ordering = ('code',)
    
    def cuts_count(self, obj):
        count = obj.stone_cuts.count()
        return format_html('<span style="color:#D4AF37; font-weight:bold;">{}</span>', count)
    cuts_count.short_description = 'عدد الأصناف'


@admin.register(StoneCut)
class StoneCutAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'category_group', 'description', 'models_count')
    list_filter = ('category_group',)
    search_fields = ('code', 'name')
    ordering = ('code',)
    
    def models_count(self, obj):
        count = obj.models.count()
        return format_html('<span style="color:#2196F3; font-weight:bold;">{}</span>', count)
    models_count.short_description = 'عدد الموديلات'


@admin.register(StoneModel)
class StoneModelAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'stone_cut', 'sizes_count')
    list_filter = ('stone_cut',)
    search_fields = ('code', 'name')
    ordering = ('stone_cut', 'code')
    
    def sizes_count(self, obj):
        count = obj.sizes.count()
        return format_html('<span style="color:#D4AF37; font-weight:bold;">{}</span>', count)
    sizes_count.short_description = 'عدد المقاسات'


@admin.register(StoneSize)
class StoneSizeAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'stone_cut', 'stone_model', 'stone_type_display', 'short_code',
                    'weight_range', 'size_mm', 'price_display', 'color', 'clarity')
    list_filter = ('stone_cut', 'stone_model', 'color', 'clarity')
    search_fields = ('code', 'stone_type', 'short_code')
    ordering = ('code',)
    list_per_page = 50
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('code', 'short_code'), ('stone_cut', 'stone_model'), 'stone_type')
        }),
        ('الوزن والمقاس', {
            'fields': (('weight_from', 'weight_to'), 'size_mm')
        }),
        ('التسعير والجودة', {
            'fields': ('price_per_carat', ('color', 'clarity'))
        }),
    )
    
    def stone_type_display(self, obj):
        return format_html('<span style="color:#9C27B0;">{}</span>', obj.stone_type or '-')
    stone_type_display.short_description = 'نوع الحجر'
    
    def weight_range(self, obj):
        return format_html('{} - {}', obj.weight_from, obj.weight_to)
    weight_range.short_description = 'نطاق الوزن'
    
    def price_display(self, obj):
        return format_html('<span style="color:#4CAF50; font-weight:bold;">{}</span>', obj.price_per_carat)
    price_display.short_description = 'سعر القراط'


@admin.register(Stone)
class StoneAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'stone_type', 'stone_cut', 'current_stock', 'unit')
    list_filter = ('stone_type', 'stone_cut')
    search_fields = ('name',)

@admin.register(InstallationTool)
class InstallationToolAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'tool_type_badge', 'stock_display', 'unit', 'carat', 'stock_status')
    list_filter = ('tool_type', 'unit', 'carat')
    search_fields = ('name', 'description')
    list_editable = ('unit',)
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name', 'description', 'tool_type', 'unit')
        }),
        ('المخزون (للعدد)', {
            'fields': (('quantity', 'min_quantity'),),
            'description': 'للأدوات المحسوبة بالعدد'
        }),
        ('المخزون (للوزن)', {
            'fields': (('weight', 'min_weight'), 'carat'),
            'description': 'للأدوات الذهبية المحسوبة بالوزن'
        }),
    )
    
    # Disable browser autocomplete
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['name'].widget.attrs['autocomplete'] = 'off'
        form.base_fields['description'].widget.attrs['autocomplete'] = 'off'
        return form
    
    def tool_type_badge(self, obj):
        colors = {
            'consumable': '#FF9800',
            'equipment': '#2196F3',
            'spare_part': '#9C27B0',
            'gold_wire': '#D4AF37',
            'gold_solder': '#FFD700',
            'cadmium': '#C0C0C0',
            'gold_sheet': '#B8860B',
        }
        color = colors.get(obj.tool_type, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; font-weight:bold;">{}</span>',
            color, color, obj.get_tool_type_display()
        )
    tool_type_badge.short_description = 'النوع'
    
    def stock_display(self, obj):
        if obj.unit == 'gram':
            return format_html('<span style="color:#D4AF37; font-weight:bold;">{} جم</span>', obj.weight)
        return format_html('<span style="font-weight:bold;">{}</span>', obj.quantity)
    stock_display.short_description = 'الرصيد'
    
    def stock_status(self, obj):
        if obj.unit == 'gram':
            is_low = obj.weight <= obj.min_weight
        else:
            is_low = obj.quantity <= obj.min_quantity
        
        if is_low:
            return mark_safe('<span style="color:#f44336; font-weight:bold;">⚠️ يحتاج طلب</span>')
        return mark_safe('<span style="color:#4CAF50;">✓ متوفر</span>')
    stock_status.short_description = 'الحالة'

@admin.register(WorkshopSettlement)
class WorkshopSettlementAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('workshop', 'settlement_type', 'amount', 'weight', 'gross_weight', 'date')
    list_filter = ('settlement_type', 'workshop')
    search_fields = ('reference', 'notes')

@admin.register(Workshop)
class WorkshopAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'workshop_type_badge', 'contact_person', 'phone', 'gold_summary', 'filings_summary', 'labor_balance_display')
    list_filter = ('workshop_type',)
    search_fields = ('name', 'contact_person')
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('name', 'workshop_type'), ('contact_person', 'phone'), 'address')
        }),
        ('الأرصدة الحالية (العهدة - ذهب)', {
            'fields': (('gold_balance_18', 'gold_balance_21', 'gold_balance_24'),),
            'description': 'تمثل هذه الأرصدة كمية الذهب الموجودة بعهدة الورشة حالياً.'
        }),
        ('الأرصدة الحالية (العهدة - براده)', {
            'fields': (('filings_balance_18', 'filings_balance_21', 'filings_balance_24'),),
            'description': 'تمثل هذه الأرصدة كمية البراده/البودر الموجودة بعهدة الورشة حالياً.'
        }),
        ('الحساب المالي', {
            'fields': ('labor_balance',),
            'description': 'رصيد المصنعيات والنقدية.'
        }),
    )

    def gold_summary(self, obj):
        return format_html(
            '<div style="font-size: 0.85rem;">'
            '<span style="color:#B8860B;">18: <b>{}</b></span><br>'
            '<span style="color:#D4AF37;">21: <b>{}</b></span><br>'
            '<span style="color:#FFD700;">24: <b>{}</b></span>'
            '</div>',
            obj.gold_balance_18, obj.gold_balance_21, obj.gold_balance_24
        )
    gold_summary.short_description = "أرصدة الذهب"

    def filings_summary(self, obj):
        return format_html(
            '<div style="font-size: 0.85rem; opacity:0.8;">'
            '18: {}<br>21: {}<br>24: {}'
            '</div>',
            obj.filings_balance_18, obj.filings_balance_21, obj.filings_balance_24
        )
    filings_summary.short_description = "أرصدة البرادة"

    def labor_balance_display(self, obj):
        return format_html('<span style="color:#4CAF50; font-weight:bold;">{} ج.م</span>', obj.labor_balance)
    labor_balance_display.short_description = "رصيد مالي"

    def workshop_type_badge(self, obj):
        color = '#2196F3' if obj.workshop_type == 'internal' else '#9C27B0'
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; font-weight:bold; font-size:11px;">{}</span>',
            color, color, obj.get_workshop_type_display()
        )
    workshop_type_badge.short_description = 'النوع'

@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('order_number_display', 'status_badge', 'carat', 'workshop', 'weight_summary', 'manufacturing_progress', 'manufacturing_pay_display', 'resulting_item_display', 'actions_column')
    list_display_links = ('order_number_display',)
    list_filter = ('status', 'carat', 'workshop')
    search_fields = ('order_number', 'assigned_technician', 'workshop__name')
    inlines = [OrderStoneInline, OrderToolInline, ProductionStageInline]
    list_per_page = 20
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('بيانات الأمر والورشة', {
            'fields': (
                ('order_number', 'workshop', 'status'),
                ('carat', 'assigned_technician'),
                ('start_date', 'end_date', 'print_job_card_link'),
            )
        }),
        ('موازين الذهب والخسية', {
            'fields': (
                ('input_material', 'input_weight'),
                ('output_weight', 'powder_weight', 'scrap_weight'),
                ('scrap_percentage_display', 'manufacturing_progress')
            ),
        }),
        ('الأحجار والمصنعية', {
            'fields': (
                ('total_stone_weight', 'labor_rate', 'manufacturing_pay'),
            )
        }),
        ('فحص الجودة (QC)', {
            'fields': (
                ('qc_technician', 'qc_notes'),
                'final_product_image_display',
                'final_product_image'
            ),
        }),
        ('الأتمتة وتوليد الأصناف', {
            'classes': ('collapse',),
            'fields': (
                'auto_create_item', 'item_name_pattern', 'target_branch'
            ),
            'description': 'سيتم إنشاء صنف في المخزن تلقائياً عند تحويل الحالة إلى "مكتمل".'
        }),
    )
    
    readonly_fields = ('start_date', 'scrap_percentage_display', 'manufacturing_progress', 'resulting_item_display', 'print_job_card_link', 'final_product_image_display')

    def order_number_display(self, obj):
        return format_html(
            '<span style="font-family:monospace; font-weight:bold; color:#D4AF37; font-size:14px;">{}</span>',
            obj.order_number
        )
    order_number_display.short_description = 'رقم الأمر'
    order_number_display.admin_order_field = 'order_number'

    def status_badge(self, obj):
        status_colors = {
            'draft': ('#9E9E9E', 'مسودة'),
            'pending': ('#FF9800', 'قيد الانتظار'),
            'in_progress': ('#2196F3', 'تحت التشغيل'),
            'completed': ('#4CAF50', 'مكتمل'),
            'cancelled': ('#f44336', 'ملغي'),
            'casting': ('#9C27B0', 'سبك'),
            'crafting': ('#FF5722', 'تشكيل'),
            'polishing': ('#00BCD4', 'جاهز'),
            'qc_pending': ('#f39c12', 'قيد فحص الجودة'),
            'qc_failed': ('#e74c3c', 'فحص جودة مرفوض'),
        }
        color, label = status_colors.get(obj.status, ('#666', obj.status))
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; '
            'font-size:12px; font-weight:bold; border:1px solid {}44; white-space:nowrap;">{}</span>',
            color, color, color, label
        )
    status_badge.short_description = 'الحالة'
    status_badge.admin_order_field = 'status'

    def weight_summary(self, obj):
        input_w = float(obj.input_weight or 0)
        output_w = float(obj.output_weight or 0)
        powder_w = float(obj.powder_weight or 0)
        scrap_w = float(obj.scrap_weight or 0)
        tools_w = float(obj.get_total_tools_weight() or 0)
        
        # New base for scrap: Input + Tools
        total_input = input_w + tools_w
        scrap_color = '#4CAF50' if scrap_w <= (total_input * 0.05) else '#f44336'
        
        return format_html(
            '<div style="font-size:12px; line-height:1.6; white-space:nowrap;">'
            '<div><strong>داخل:</strong> <span style="color:#2196F3;">{}</span> ج</div>'
            '<div><strong>إضافات:</strong> <span style="color:#D4AF37;">{}</span> ج</div>'
            '<div><strong>خارج:</strong> <span style="color:#4CAF50;">{}</span> ج</div>'
            '<div><strong>بودر:</strong> <span style="color:#D4AF37;">{}</span> ج</div>'
            '<div><strong>هالك:</strong> <span style="color:{};">{}</span> ج</div>'
            '</div>',
            input_w, tools_w, output_w, powder_w, scrap_color, scrap_w
        )
    weight_summary.short_description = 'الأوزان'

    def actions_column(self, obj):
        if obj.id:
            return format_html(
                '<div style="display:flex; gap:5px; white-space:nowrap;">'
                '<a href="/manufacturing/order/{}/print/" target="_blank" title="طباعة كارت الشغل" '
                'style="background:#2196F3; color:white; padding:6px 10px; border-radius:5px; text-decoration:none; font-size:12px;">'
                '<i class="fa-solid fa-print"></i>'
                '</a>'
                '</div>',
                obj.id
            )
        return "-"
    actions_column.short_description = 'إجراءات'

    def print_job_card_link(self, obj):
        if obj.id:
            return format_html(
                '<a href="/manufacturing/order/{}/print/" target="_blank" class="button" style="background:#2196F3; color:white; font-weight:bold;">'
                '<i class="fa-solid fa-print"></i> طباعة كارت الشغل'
                '</a>', 
                obj.id
            )
        return "-"
    print_job_card_link.short_description = 'كارت الشغل'

    def resulting_item_display(self, obj):
        if obj.resulting_item:
            return format_html(
                '<a href="/inventory/print-tags/?ids={}" target="_blank" class="button" style="background:#D4AF37; color:black; font-weight:bold;">'
                '<i class="fa-solid fa-barcode"></i> طباعة الباركود ({})'
                '</a>', 
                obj.resulting_item.id, obj.resulting_item.barcode
            )
        return mark_safe('<span style="color:#666;">لم يتم التوليد بعد</span>')
    resulting_item_display.short_description = 'القطعة المنتجة'

    def final_product_image_display(self, obj):
        if obj.final_product_image:
            return format_html('<img src="{}" style="max-height: 200px; border-radius: 10px; border: 1px solid #333;"/>', obj.final_product_image.url)
        return mark_safe('<span style="color:#666;">لا توجد صورة للمنتج النهائي</span>')
    final_product_image_display.short_description = 'صورة المنتج النهائي'

    def save_model(self, request, obj, form, change):
        # Calculate scrap automatically including tools weight
        if obj.input_weight and obj.output_weight:
            tools_weight = obj.get_total_tools_weight()
            powder = obj.powder_weight or 0
            # Formula: (Input + Tools) - (Output + Powder) = Scrap
            obj.scrap_weight = (obj.input_weight + tools_weight) - (obj.output_weight + powder)
        
        if obj.labor_rate and obj.output_weight:
            if not obj.manufacturing_pay or obj.manufacturing_pay == 0:
                obj.manufacturing_pay = obj.labor_rate * obj.output_weight

        super().save_model(request, obj, form, change)
    
    def manufacturing_pay_display(self, obj):
        return format_html('<span style="color:#4CAF50; font-weight:bold;">{} ج.م</span>', obj.manufacturing_pay)
    manufacturing_pay_display.short_description = "أجر التصنيع"

    def manufacturing_progress(self, obj):
        stages = {
            'draft': 0, 'casting': 25, 'crafting': 50, 'polishing': 75, 'completed': 100,
        }
        progress = stages.get(obj.status, 0)
        color = "#D4AF37" if progress < 100 else "#4CAF50"
        return format_html(
            '<div style="width:100%; max-width:200px; background:#111; border-radius:10px; overflow:hidden; border:1px solid #333; height:12px;">'
            '<div style="width:{}%; background:{}; height:100%; transition: width 0.5s ease-in-out;"></div>'
            '</div>', 
            progress, color
        )
    manufacturing_progress.short_description = 'حالة التنفيذ'

    def scrap_percentage_display(self, obj):
        if obj.input_weight and obj.scrap_weight is not None and obj.input_weight > 0:
            percent = (obj.scrap_weight / obj.input_weight) * 100
            
            # Use the 0.5% - 1.0% range
            if 0.5 <= percent <= 1.0:
                color = "#4CAF50" # Green
                icon = '<i class="fa-solid fa-check-double" style="margin-right:5px;"></i>'
                label = "مثالي (ضمن النطاق)"
            elif percent < 0.5:
                color = "#2196F3" # Blue (Too low/Extraordinary)
                icon = '<i class="fa-solid fa-circle-info" style="margin-right:5px;"></i>'
                label = "منخفض جداً"
            else:
                color = "#ff4b2b" # Red (High)
                icon = '<i class="fa-solid fa-triangle-exclamation" style="margin-right:5px;"></i>'
                label = "خسية مرتفعة"

            return format_html(
                '<div style="display:flex; align-items:center; gap:10px;">'
                '<span style="background:{}22; color:{}; padding:5px 15px; border-radius:8px; border:1px solid {}44; font-weight:bold;">{}%</span>'
                '<span style="color:{}; font-size:0.85rem;">{} {}</span>'
                '</div>', 
                color, color, color, f"{percent:.2f}", color, mark_safe(icon), label
            )
        return mark_safe('<span style="color:#555;">0%</span>')
    scrap_percentage_display.short_description = 'نسبة الهالك (مع التنبيه)'
    
    class Media:
        js = ('js/manufacturing_alarm.js', 'js/inline_table_fix.js')

@admin.register(WorkshopTransfer)
class WorkshopTransferAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('transfer_number', 'from_workshop', 'to_workshop', 'carat', 'weight_display', 'status_badge', 'date')
    list_filter = ('status', 'carat', 'from_workshop', 'to_workshop')
    search_fields = ('transfer_number', 'notes')
    readonly_fields = ('initiated_by', 'confirmed_by', 'date')
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('transfer_number', 'date'), ('from_workshop', 'to_workshop'))
        }),
        ('تفاصيل الوزن', {
            'fields': (('carat', 'weight'), 'status')
        }),
        ('التتبع والتوثيق', {
            'fields': (('initiated_by', 'confirmed_by'), 'notes')
        }),
    )

    def weight_display(self, obj):
        return format_html('<span style="color:#D4AF37; font-weight:bold;">{} جم</span>', obj.weight)
    weight_display.short_description = 'الوزن'

    def status_badge(self, obj):
        colors = {
            'pending': '#FF9800',
            'completed': '#4CAF50',
            'cancelled': '#f44336',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; font-weight:bold;">{}</span>',
            color, color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.initiated_by = request.user
        if obj.status == 'completed' and not obj.confirmed_by:
            obj.confirmed_by = request.user
        super().save_model(request, obj, form, change)
