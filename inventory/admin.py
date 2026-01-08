from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Item, RawMaterial, ItemTransfer, MaterialTransfer
from core.admin_mixins import ExportImportMixin

@admin.register(Category)
class CategoryAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'barcode_prefix')
    list_editable = ('barcode_prefix',)

@admin.register(Item)
class ItemAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('item_thumbnail', 'barcode_img', 'name', 'category', 'carat', 'weight_details', 'total_overhead_display', 'total_manufacturing_cost_display', 'status_badge', 'current_branch')
    list_filter = ('category', 'carat', 'status', 'current_branch')
    search_fields = ('barcode', 'name', 'rfid_tag')
    list_per_page = 20
    list_display_links = ('item_thumbnail', 'name')
    actions = ['print_tags_action', 'initiate_transfer_action']
    
    def print_tags_action(self, request, queryset):
        ids = ",".join([str(item.id) for item in queryset])
        from django.shortcuts import redirect
        return redirect(f'/inventory/print-tags/?ids={ids}')
    print_tags_action.short_description = "طباعة باركود القطع المختارة"

    def initiate_transfer_action(self, request, queryset):
        # Redirect to ItemTransfer add page with selected items
        ids = [str(item.id) for item in queryset]
        from django.shortcuts import redirect
        from django.urls import reverse
        url = reverse('admin:inventory_itemtransfer_add')
        return redirect(f"{url}?items={','.join(ids)}")
    initiate_transfer_action.short_description = "🚚 بدء عملية تحويل للقطع المختارة"

    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': (('barcode', 'name'), ('category', 'carat'), 'status')
        }),
        ('تفاصيل الأوزان (بالجرام)', {
            'fields': (('gross_weight', 'stone_weight', 'net_gold_weight'),),
            'description': 'يرجى إدخال الأوزان بدقة 3 فواصل عشرية'
        }),
        ('التسعير والمصنعية', {
            'fields': (('labor_fee_per_gram', 'fixed_labor_fee'),),
        }),
        ('تكاليف المصنع (الموزعة من أمر التصنيع)', {
            'fields': (
                ('overhead_electricity', 'overhead_water'),
                ('overhead_gas', 'overhead_rent'),
                ('overhead_salaries', 'overhead_other'),
                'total_overhead_display',
                'total_manufacturing_cost_display',
            ),
            'classes': ('collapse',),
            'description': 'هذه القيم يتم تحديثها تلقائياً عند تطبيق توزيع التكاليف في قسم التصنيع.'
        }),
        ('التتبع والموقع', {
            'fields': (('rfid_tag', 'current_branch'), 'image'),
        }),
        ('تقرير دورة حياة المنتج (التصنيع)', {
            'fields': ('production_lifecycle_report',),
            'classes': ('collapse',),
            'description': 'تقرير تفصيلي عن رحلة القطعة خلال مراحل التصنيع المختلفة بالأوزان والتواريخ.'
        }),
    )

    readonly_fields = ('barcode_img', 'weight_details', 'item_thumbnail', 'total_overhead_display', 'total_manufacturing_cost_display', 'production_lifecycle_report')
    
    class Media:
        js = ('admin/js/auto_barcode.js',)

    def production_lifecycle_report(self, obj):
        if not obj or not obj.source_order:
            return "هذه القطعة غير مرتبطة بأمر تصنيع مباشر، أو تم إدخالها كمخزون افتتاحي."
            
        order = obj.source_order
        stages = order.stages.all().order_by('timestamp')
        
        if not stages.exists():
            return "مربوطة بأمر تصنيع ولكن لا توجد مراحل مسجلة."
            
        html = """
        <style>
            .lifecycle-table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 10px; }}
            .lifecycle-table th {{ background: rgba(255,255,255,0.05); padding: 8px; text-align: right; border: 1px solid rgba(255,255,255,0.1); color: var(--gold-primary); }}
            .lifecycle-table td {{ padding: 8px; border: 1px solid rgba(255,255,255,0.1); color: #ddd; }}
            .lifecycle-table tr:hover {{ background: rgba(255,255,255,0.02); }}
            .loss-bad {{ color: #f44336; font-weight: bold; }}
        </style>
        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="margin-bottom: 10px; font-size: 12px; color: #aaa;">
                <strong>أمر التصنيع:</strong> <a href="/admin/manufacturing/manufacturingorder/{}/change/" target="_blank" style="color: var(--gold-primary);">{}</a> | 
                <strong>تاريخ البدء:</strong> {}
            </div>
            <table class="lifecycle-table">
                <thead>
                    <tr>
                        <th>المرحلة / الورشة</th>
                        <th>الفني</th>
                        <th>التاريخ (خروج)</th>
                        <th>الوقت المستغرق</th>
                        <th>وزن مستلم</th>
                        <th>وزن خارج</th>
                        <th>خسية (هالك)</th>
                        <th>بودر (برادة)</th>
                    </tr>
                </thead>
                <tbody>
        """.format(order.id, order.order_number, order.start_date.strftime('%Y-%m-%d'))
        
        for stage in stages:
            # Calculate duration
            duration_str = "-"
            if stage.start_datetime and stage.end_datetime:
                diff = stage.end_datetime - stage.start_datetime
                # Simple formatting
                days = diff.days
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                duration_str = f"{hours}h {minutes}m"
                if days > 0:
                    duration_str = f"{days}d {duration_str}"
            elif stage.timestamp:
                 duration_str = stage.timestamp.strftime("%H:%M") # fallback

            # Styling for loss
            loss_class = "loss-bad" if stage.loss_weight > 0 else ""
            
            html += f"""
                <tr>
                    <td>
                        <strong>{stage.get_stage_name_display()}</strong><br>
                        <span style="color:#888;">{stage.workshop.name if stage.workshop else '-'}</span>
                    </td>
                    <td>{stage.technician or '-'}</td>
                    <td>{stage.end_datetime.strftime('%Y-%m-%d %I:%M %p') if stage.end_datetime else '-'}</td>
                    <td dir="ltr" style="text-align:right;">{duration_str}</td>
                    <td>{stage.input_weight:,.3f} g</td>
                    <td>{stage.output_weight:,.3f} g</td>
                    <td class="{loss_class}">{stage.loss_weight:,.3f} g</td>
                    <td>{stage.powder_weight:,.3f} g</td>
                </tr>
            """
            
        html += """
                </tbody>
            </table>
        </div>
        """
        return mark_safe(html)
    
    production_lifecycle_report.short_description = "تقرير التصنيع التفصيلي"

    def total_overhead_display(self, obj):
        val = float(obj.total_overhead or 0)
        return format_html('<span style="color:#FF9800; font-weight:bold;">{} ج.م</span>', f"{val:,.2f}")
    total_overhead_display.short_description = 'إجمالي التكاليف الصناعية'

    def total_manufacturing_cost_display(self, obj):
        val = float(obj.total_manufacturing_cost or 0)
        return format_html('<span style="color:#2196F3; font-weight:bold; font-size:14px;">{} ج.م</span>', f"{val:,.2f}")
    total_manufacturing_cost_display.short_description = 'التكلفة الكلية (صناعي + أجر)'

    def item_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:50px; height:50px; border-radius:10px; object-fit:cover; border:1px solid var(--gold-soft); shadow:var(--shadow-sm);" />', obj.image.url)
        return mark_safe('<div style="width:50px; height:50px; border-radius:10px; background:rgba(255,255,255,0.03); border:1px dashed rgba(255,255,255,0.1); display:flex; align-items:center; justify-content:center; color:#555;"><i class="fa-solid fa-image"></i></div>')
    item_thumbnail.short_description = 'الصورة'

    def weight_details(self, obj):
        return format_html(
            '<div style="line-height:1.5;">'
            '<b style="color:var(--gold-primary);">{}g</b> <small>صافي</small><br>'
            '<span style="color:#888; font-size:0.8rem;">{}g فصوص</span>'
            '</div>',
            obj.net_gold_weight if obj.net_gold_weight else 0, 
            obj.stone_weight if obj.stone_weight else 0
        )
    weight_details.short_description = 'تفاصيل الوزن'

    def status_badge(self, obj):
        colors = {
            'available': '#4CAF50', 'sold': '#aaa', 'manufacturing': '#D4AF37', 'mandoob': '#2196F3', 'lost': '#ff4b2b',
        }
        color = colors.get(obj.status, '#fff')
        return format_html(
            '<span style="background:{}22; color:{}; padding:5px 12px; border-radius:12px; font-size:0.85rem; border:1px solid {}44; font-weight:600;">{}</span>',
            color, color, color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    def barcode_img(self, obj):
        # Basic placeholder for barcode visualization
        return format_html('<span style="font-family: monospace; background: #eee; padding: 2px 5px; border-radius: 3px;">{}</span>', obj.barcode)
    barcode_img.short_description = 'الباركود'

@admin.register(RawMaterial)
class RawMaterialAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('material_icon', 'name', 'material_type', 'carat', 'weight_badge', 'branch')
    list_filter = ('material_type', 'carat', 'branch')
    search_fields = ('name',)
    list_display_links = ('material_icon', 'name')

    def material_icon(self, obj):
        return mark_safe('<div style="font-size:1.2rem; color:var(--gold-primary);"><i class="fa-solid fa-coins"></i></div>')
    material_icon.short_description = ''

    def weight_badge(self, obj):
        return format_html('<span style="color:white; font-weight:bold;">{} <small>g</small></span>', obj.current_weight)
    weight_badge.short_description = 'الوزن الحالي'

@admin.register(ItemTransfer)
class ItemTransferAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('transfer_number', 'from_branch', 'to_branch', 'items_count', 'status_badge', 'date', 'initiated_by')
    list_filter = ('status', 'from_branch', 'to_branch', 'date')
    search_fields = ('transfer_number', 'notes')
    filter_horizontal = ('items',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.initiated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if 'items' in request.GET:
            initial['items'] = request.GET['items'].split(',')
        return initial

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'عدد القطع'

    def status_badge(self, obj):
        colors = {'pending': '#FF9800', 'completed': '#4CAF50', 'cancelled': '#f44336'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:15px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

@admin.register(MaterialTransfer)
class MaterialTransferAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('transfer_number', 'from_branch', 'to_branch', 'material', 'weight_display', 'status_badge', 'date')
    list_filter = ('status', 'from_branch', 'to_branch', 'date')
    search_fields = ('transfer_number', 'notes')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.initiated_by = request.user
        super().save_model(request, obj, form, change)

    def weight_display(self, obj):
        return format_html('<b style="color:var(--gold-primary);">{} g</b>', obj.weight)
    weight_display.short_description = 'الوزن'

    def status_badge(self, obj):
        colors = {'pending': '#FF9800', 'completed': '#4CAF50', 'cancelled': '#f44336'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:15px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'
