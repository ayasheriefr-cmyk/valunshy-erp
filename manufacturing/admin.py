from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Workshop, WorkshopSettlement, ManufacturingCylinder,
    StoneCategoryGroup, StoneCut, StoneModel, StoneSize, Stone,
    StoneInventoryAudit,
    InstallationTool, ManufacturingOrder, OrderStone, OrderTool,
    ProductionStage, WorkshopTransfer, CostAllocation
)
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
            return mark_safe('<span style="color:#4CAF50;">✓ لا يوجد</span>')
        return '-'
    quantity_broken_display.short_description = 'الكسر/الفقد'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "production_stage":
            try:
                # Attempt to retrieve the order ID from height in the usage context (URL)
                # Note: This works for the change view of the parent model
                resolved = request.resolver_match
                if resolved and resolved.kwargs.get('object_id'):
                    order_id = resolved.kwargs.get('object_id')
                    kwargs["queryset"] = ProductionStage.objects.filter(order_id=order_id)
                else:
                    # If this is a new order (add view), no stages exist yet usually, 
                    # or we can't filter easily. Return empty or all?
                    # Usually better to return none or all. But practically, distinct stages are created *with* the order.
                    # If it's an add view, we might not be able to filter effectively until saved.
                    pass
            except Exception:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
class StoneCutAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category_group')
    list_filter = ('category_group',)
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(StoneModel)
class StoneModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'stone_cut')
    list_filter = ('stone_cut',)
    search_fields = ('code', 'name')
    ordering = ('stone_cut', 'code')


@admin.register(StoneSize)
class StoneSizeAdmin(admin.ModelAdmin):
    list_display = ('code', 'stone_cut', 'stone_model', 'size_mm', 'color', 'clarity', 'price_per_carat')
    list_filter = ('stone_cut', 'color', 'clarity')
    search_fields = ('code',)
    ordering = ('code',)
    list_per_page = 50
    

@admin.register(StoneInventoryAudit)
class StoneInventoryAuditAdmin(admin.ModelAdmin):
    list_display = ('audit_date', 'stone', 'system_stock', 'physical_stock', 'difference', 'system_quantity', 'physical_quantity', 'difference_quantity', 'audited_by')
    list_filter = ('audit_date', 'stone__stone_cut__category_group')
    search_fields = ('stone__name', 'notes')
    readonly_fields = ('difference', 'difference_quantity')
    date_hierarchy = 'audit_date'
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('audit_date', 'stone', 'audited_by', 'notes')
        }),
        ('جرد الوزن (قيراط/جرام)', {
            'fields': (('system_stock', 'physical_stock'), 'difference')
        }),
        ('جرد العدد (قطعة)', {
            'fields': (('system_quantity', 'physical_quantity'), 'difference_quantity')
        }),
    )

@admin.register(Stone)
class StoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'stone_type', 'stone_cut', 'stone_size', 'current_stock', 'current_quantity', 'unit')
    list_filter = ('stone_type', 'unit', 'stone_cut__category_group')
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
    list_display = ('order_number_display', 'status_badge', 'carat', 'workshop', 'weight_summary', 'manufacturing_progress', 'total_overhead_display', 'total_making_cost_display', 'actions_column')
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
        ('تكاليف المصنع (الموزعة)', {
            'fields': (
                'cost_allocation',
                ('overhead_electricity', 'overhead_water'),
                ('overhead_gas', 'overhead_rent'),
                ('overhead_salaries', 'overhead_other'),
                'total_overhead_display',
                'total_making_cost_display',
            ),
            'classes': ('collapse',),
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
    
    readonly_fields = ('start_date', 'scrap_percentage_display', 'manufacturing_progress', 'resulting_item_display', 'print_job_card_link', 'final_product_image_display', 'total_overhead_display', 'total_making_cost_display')

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
    
    def total_overhead_display(self, obj):
        val = float(obj.total_overhead or 0)
        return format_html('<span style="color:#FF9800; font-weight:bold;">{} ج.م</span>', f"{val:,.2f}")
    total_overhead_display.short_description = 'إجمالي التكاليف الصناعية'
    
    def total_making_cost_display(self, obj):
        val = float(obj.total_making_cost or 0)
        return format_html('<span style="color:#2196F3; font-weight:bold; font-size:15px;">{} ج.م</span>', f"{val:,.2f}")
    total_making_cost_display.short_description = 'التكلفة الكلية للتصنيع'
    
    class Media:
        js = ('js/manufacturing_alarm.js', 'js/inline_table_fix.js')

    actions = ['merge_orders_action']

    def merge_orders_action(self, request, queryset):
        """
        Custom action to merge multiple manufacturing orders into one main order.
        """
        if 'confirm' in request.POST:
            main_order_id = request.POST.get('main_order_id')
            if not main_order_id:
                self.message_user(request, "يرجى اختيار الأمر الأساسي.", level='error')
                return None

            try:
                main_order = ManufacturingOrder.objects.get(id=main_order_id)
                other_orders = queryset.exclude(id=main_order_id)
                
                if not other_orders.exists():
                    self.message_user(request, "يجب اختيار أمرين على الأقل للدمج.", level='error')
                    return None

                total_added_input = 0
                merged_numbers = []

                for order in other_orders:
                    # 1. Sum Weights
                    total_added_input += (order.input_weight or 0)
                    merged_numbers.append(order.order_number)

                    # 2. Transfer Stones
                    for stone in order.orderstone_set.all():
                        stone.order = main_order
                        stone.save()

                    # 3. Transfer Tools
                    for tool in order.order_tools_list.all():
                        tool.order = main_order
                        tool.save()

                    # 4. Transfer Production Stages
                    for stage in order.stages.all():
                        stage.order = main_order
                        stage.save()

                    # 5. Mark as Merged
                    order.status = 'merged'
                    order.save()

                # Update Main Order
                main_order.input_weight += total_added_input
                merge_note = f"\n[دمج]: تم دمج الأوامر التالية في هذا الأمر: {', '.join(merged_numbers)}"
                main_order.qc_notes = (main_order.qc_notes or "") + merge_note
                main_order.save()

                self.message_user(request, f"تم دمج {other_orders.count()} أمر في الأمر {main_order.order_number} بنجاح.")
                return None

            except Exception as e:
                self.message_user(request, f"خطأ أثناء الدمج: {str(e)}", level='error')
                return None

        # If not confirmed, show confirmation page
        from django.template.response import TemplateResponse
        context = {
            'orders': queryset,
            'title': "دمج أوامر التصنيع",
            'LANGUAGE_CODE': getattr(request, 'LANGUAGE_CODE', 'ar'),
        }
        return TemplateResponse(request, "admin/manufacturing/merge_confirmation.html", context)
    
    merge_orders_action.short_description = "🔗 دمج الأوامر المختارة (منتج واحد)"

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

@admin.register(CostAllocation)
class CostAllocationAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('period_name', 'start_date', 'end_date', 'total_overhead_display', 'allocation_basis', 'status_badge', 'orders_count')
    list_filter = ('status', 'allocation_basis')
    search_fields = ('period_name',)
    
    readonly_fields = (
        'total_overhead_display', 
        'total_labor_income_display', 
        'total_labor_cost_display', 
        'net_labor_profit_display', 
        'total_production_weight_display',
        'total_production_weight_snapshot', # Actual non-editable field
        'total_labor_cost_snapshot',        # Actual non-editable field
        'total_labor_income_snapshot',      # Actual non-editable field
        'net_labor_profit_snapshot',         # Actual non-editable field
        'created_at', 'updated_at', 'orders_count'
    )

    fieldsets = (
        ('الفترة الزمنية', {
            'fields': (('period_name',), ('start_date', 'end_date'))
        }),
        ('إجمالي التكاليف التشغيلية', {
            'fields': (
                ('total_electricity', 'total_water'),
                ('total_gas', 'total_rent'),
                ('total_salaries', 'total_other'),
            ),
            'description': 'سيتم توزيع هذه المصاريف على الأوامر بناءً على أساس التوزيع المختار.'
        }),
        ('إعدادات التوزيع والفرع', {
            'fields': (('allocation_basis', 'status'), ('cost_center',))
        }),
        ('ميزان الأجور ونتائج التصنيع', {
            'fields': (
                ('total_labor_income_display', 'total_labor_cost_display'),
                ('total_overhead_display', 'net_labor_profit_display'),
                'total_production_weight_display'
            ),
            'description': 'يوضح هذا القسم ربحية قطاع التصنيع بعد خصم أجور الورش وكافة المصاريف التشغيلية.'
        }),
        ('إحصائيات النظام (تقني)', {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',)
        }),
    )

    # --- Display Methods ---
    
    def total_production_weight_display(self, obj):
        val = float(obj.total_production_weight_snapshot or 0)
        return format_html('<span style="font-weight:bold;">{} جم</span>', f"{val:,.2f}")
    total_production_weight_display.short_description = 'إجمالي الوزن المنتج'

    def total_labor_income_display(self, obj):
        val = float(obj.total_labor_income_snapshot or 0)
        return format_html('<span style="color:#2196F3; font-weight:bold; font-size:1.1rem;">{} ج.م</span>', f"{val:,.2f}")
    total_labor_income_display.short_description = 'إجمالي دخل المصنعية'

    def total_labor_cost_display(self, obj):
        val = float(obj.total_labor_cost_snapshot or 0)
        return format_html('<span style="color:#f44336; font-weight:bold;">{} ج.م</span>', f"{val:,.2f}")
    total_labor_cost_display.short_description = 'أجور الورش الخارجية'
    
    def total_overhead_display(self, obj):
        val = float(obj.total_overhead_amount or 0)
        return format_html('<span style="color:#607D8B; font-weight:bold;">{} ج.م</span>', f"{val:,.2f}")
    total_overhead_display.short_description = 'إجمالي مصاريف التشغيل'

    def net_labor_profit_display(self, obj):
        profit = float(obj.net_labor_profit_snapshot or 0)
        color = '#4CAF50' if profit >= 0 else '#f44336'
        bg = 'rgba(76, 175, 80, 0.1)' if profit >= 0 else 'rgba(244, 67, 54, 0.1)'
        return format_html(
            '<div style="background:{}; color:{}; padding:10px 20px; border-radius:10px; text-align:center; border:2px solid {};">'
            '<span style="font-size:1.3rem; font-weight:900;">{} ج.م</span><br>'
            '<small style="font-weight:bold; opacity:0.8;">صافي نتيجة التصنيع</small>'
            '</div>',
            bg, color, color, f"{profit:,.2f}"
        )
    net_labor_profit_display.short_description = 'صافي الربح/الخسارة'

    def orders_count(self, obj):
        count = ManufacturingOrder.objects.filter(cost_allocation=obj).count()
        return format_html('<span style="font-weight:bold;">{}</span>', count)
    orders_count.short_description = 'عدد الأوامر'

    def status_badge(self, obj):
        colors = {'draft': '#FF9800', 'applied': '#4CAF50'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; font-weight:bold;">{}</span>',
            color, color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    
    actions = ['fetch_expenses_action', 'apply_cost_allocation']

    def fetch_expenses_action(self, request, queryset):
        from django.contrib import messages
        for obj in queryset:
            if obj.status == 'applied':
                messages.warning(request, f'لا يمكن جلب المصاريف لفترة مغلقة: {obj.period_name}')
                continue
            updated_count = obj.fetch_expenses()
            if updated_count > 0:
                messages.success(request, f'تم جلب وتحديث {updated_count} فئة مصاريف لفترة {obj.period_name} من الخزينة.')
            else:
                messages.info(request, f'لم يتم العثور على مصاريف جديدة مدفوعة في هذه الفترة لـ {obj.period_name}.')
    fetch_expenses_action.short_description = '🔄 جلب المصاريف من الخزينة (تلقائياً)'
    
    

    def apply_cost_allocation(self, request, queryset):
        from django.contrib import messages
        from django.db.models import Sum
        from decimal import Decimal
        
        for cost_allocation in queryset:
            if cost_allocation.status == 'applied':
                messages.warning(request, f'التكاليف "{cost_allocation.period_name}" تم ترحيلها بالفعل.')
                continue
            
            # Get all completed orders in the period
            orders = ManufacturingOrder.objects.filter(
                status='completed',
                end_date__gte=cost_allocation.start_date,
                end_date__lte=cost_allocation.end_date,
                cost_allocation__isnull=True  # Only unallocated orders
            )
            
            if not orders.exists():
                messages.warning(request, f'لا توجد أوامر مكتملة في فترة "{cost_allocation.period_name}".')
                continue
            
            # Calculate basis totals
            if cost_allocation.allocation_basis == 'weight':
                basis_total = orders.aggregate(total=Sum('output_weight'))['total'] or Decimal('0')
            else:  # labor
                basis_total = orders.aggregate(total=Sum('manufacturing_pay'))['total'] or Decimal('0')
            
            if basis_total == 0:
                messages.error(request, f'إجمالي الأساس (الوزن أو الأجر) = صفر. لا يمكن التوزيع.')
                continue
            
            # Save snapshots (Labor Audit)
            total_output_weight = orders.aggregate(total=Sum('output_weight'))['total'] or Decimal('0')
            total_external_pay = orders.filter(workshop__workshop_type='external').aggregate(total=Sum('manufacturing_pay'))['total'] or Decimal('0')
            total_factory_margin = orders.aggregate(total=Sum('factory_margin'))['total'] or Decimal('0')
            # Total Manufacturing Income from customers = (Pay to workshops) + (Margin for factory)
            total_income_from_labor = (orders.aggregate(total=Sum('manufacturing_pay'))['total'] or Decimal('0')) + total_factory_margin
            
            cost_allocation.total_production_weight_snapshot = total_output_weight
            cost_allocation.total_labor_cost_snapshot = total_external_pay
            cost_allocation.total_labor_income_snapshot = total_income_from_labor
            # Net Labor Profit = Marginal Income - Operational Overheads (Salaries, Rent, etc.)
            cost_allocation.net_labor_profit_snapshot = total_factory_margin - cost_allocation.total_overhead_amount
            
            # Distribute costs to each order
    
            for order in orders:
                if cost_allocation.allocation_basis == 'weight':
                    ratio = order.output_weight / basis_total
                else:
                    ratio = order.manufacturing_pay / basis_total
                
                order.cost_allocation = cost_allocation
                order.overhead_electricity = cost_allocation.total_electricity * ratio
                order.overhead_water = cost_allocation.total_water * ratio
                order.overhead_gas = cost_allocation.total_gas * ratio
                order.overhead_rent = cost_allocation.total_rent * ratio
                order.overhead_salaries = cost_allocation.total_salaries * ratio
                order.overhead_other = cost_allocation.total_other * ratio
                order.save()
                
                # Sync to Inventory Item if it was auto-generated
                if order.resulting_item:
                    item = order.resulting_item
                    item.overhead_electricity = order.overhead_electricity
                    item.overhead_water = order.overhead_water
                    item.overhead_gas = order.overhead_gas
                    item.overhead_rent = order.overhead_rent
                    item.overhead_salaries = order.overhead_salaries
                    item.overhead_other = order.overhead_other
                    item.save()
            
            # Mark as applied
            cost_allocation.status = 'applied'
            cost_allocation.save()
            
            messages.success(request, f'تم توزيع تكاليف "{cost_allocation.period_name}" على {orders.count()} أمر تصنيع.')
    
    apply_cost_allocation.short_description = 'احتساب وتطبيق التكاليف على الأوامر'

