from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Invoice, InvoiceItem, OldGoldReturn, SalesRepresentative, SalesRepTransaction
from core.admin_mixins import ExportImportMixin
from import_export import resources

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ('item', 'sold_weight', 'sold_gold_price', 'sold_labor_fee', 'sold_factory_cost', 'subtotal', 'total_cost_display', 'profit_display')
    readonly_fields = ('total_cost_display', 'profit_display')
    
    def total_cost_display(self, obj):
        if obj.id:
            val = float(obj.total_cost or 0)
            return format_html('<span style="color:#999; font-size: 11px;">{} ج.م</span>', f"{val:,.2f}")
        return "-"
    total_cost_display.short_description = "إجمالي التكلفة"

    def profit_display(self, obj):
        if obj.id:
            val = float(obj.profit or 0)
            color = "#4caf50" if val > 0 else "#f44336"
            return format_html('<b style="color:{};">{} ج.م</b>', color, f"{val:,.2f}")
        return "-"
    profit_display.short_description = "الربح"
    

class OldGoldReturnInline(admin.TabularInline):
    model = OldGoldReturn
    extra = 0

class SalesRepTransactionInline(admin.TabularInline):
    model = SalesRepTransaction
    extra = 0
    fields = ('transaction_type', 'invoice', 'amount', 'notes', 'created_at')
    readonly_fields = ('created_at',)

class InvoiceResource(resources.ModelResource):
    class Meta:
        model = Invoice
        fields = ('invoice_number', 'status', 'customer__name', 'branch__name', 'sales_rep__name', 'grand_total', 'payment_method', 'created_at')
        export_order = fields

@admin.register(Invoice)
class InvoiceAdmin(ExportImportMixin, admin.ModelAdmin):
    resource_class = InvoiceResource
    list_display = ('invoice_number', 'status_badge', 'customer', 'branch', 'grand_total', 'total_profit_display', 'sales_rep', 'payment_method', 'created_at')
    list_filter = ('status', 'branch', 'payment_method', 'sales_rep', 'created_at')
    search_fields = ('invoice_number', 'customer__name', 'customer__phone', 'sales_rep__name')
    inlines = [InvoiceItemInline, OldGoldReturnInline]
    readonly_fields = ('total_gold_value', 'total_labor_value', 'total_tax', 'grand_total', 'total_profit_display', 'created_by', 'created_at', 'zatca_qr_code', 'zatca_uuid', 'confirmed_by', 'confirmed_at')
    autocomplete_fields = ['sales_rep', 'customer']
    
    fieldsets = (
        ('بيانات الفاتورة الأساسية', {
            'fields': (('invoice_number', 'status'), ('branch', 'customer'), ('payment_method', 'sales_rep'))
        }),
        ('حالة التأكيد والمراجعة', {
            'fields': (('confirmed_by', 'confirmed_at'),),
            'description': 'يتم تسجيل بيانات التأكيد تلقائياً عند قيام مدير الحسابات باعتماد الفاتورة.'
        }),
        ('نظام الاستبدال (الذهب القديم)', {
            'fields': (('is_exchange', 'exchange_gold_weight', 'exchange_value_deducted'),),
            'classes': ('collapse',),
            'description': 'في حالة استبدال ذهب قديم بجديد، يرجى تفعيل الخيار وإدخال الوزن والقيمة المخصومة.'
        }),
        ('الملخص المالي والربحية (صافي)', {
            'fields': (('total_gold_value', 'total_labor_value'), ('total_tax', 'grand_total'), 'total_profit_display'),
            'classes': ('wide',)
        }),
        ('بيانات الفاتورة الإلكترونية (ZATCA)', {
            'fields': ('zatca_uuid', 'zatca_qr_code'),
            'classes': ('collapse',),
        }),
         ('بيانات السجل', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['confirm_invoices', 'reject_invoices', 'print_invoice']

    def total_profit_display(self, obj):
        val = float(obj.total_profit or 0)
        color = "#2196F3" if val > 0 else "#f44336"
        return format_html('<span style="color:{}; font-weight:bold; font-size: 16px;">{} ج.م</span>', color, f"{val:,.2f}")
    total_profit_display.short_description = "صافي الربح"

    def status_badge(self, obj):
        colors = {
            'draft': '#9e9e9e',
            'pending': '#ff9800',
            'confirmed': '#4caf50',
            'rejected': '#f44336',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background: {}; color: #fff; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "الحالة"

    def confirm_invoices(self, request, queryset):
        from django.utils import timezone
        count = 0
        for invoice in queryset.filter(status='pending'):
            invoice.status = 'confirmed'
            invoice.confirmed_by = request.user
            invoice.confirmed_at = timezone.now()
            invoice.save() # This triggers the signals
            count += 1
        self.message_user(request, f"تم تأكيد {count} فاتورة بنجاح وتأثيرها على الحسابات.")
    confirm_invoices.short_description = "✅ اعتماد وتأكيد الفواتير المختارة"

    def reject_invoices(self, request, queryset):
        count = 0
        for invoice in queryset.filter(status='pending'):
            # Return items to inventory
            for inv_item in invoice.items.all():
                item = inv_item.item
                item.status = 'available'
                item.save()
            
            invoice.status = 'rejected'
            invoice.save()
            count += 1
        self.message_user(request, f"تم رفض {count} فاتورة وإعادة الأصناف للمخزن.")
    reject_invoices.short_description = "❌ رفض الفواتير المختارة"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = "إدارة سجل فواتير المبيعات"
        return super().changelist_view(request, extra_context=extra_context)

    def print_invoice(self, request, queryset):
        pass
    print_invoice.short_description = "Print Selected Invoices (Jewelry Format)"


@admin.register(SalesRepresentative)
class SalesRepresentativeAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'address', 'user', 'phone', 'branch', 'commission_display', 'total_sales_display', 'total_commission_display', 'status_badge', 'is_active')
    list_filter = ('is_active', 'branch', 'commission_type')
    search_fields = ('name', 'phone', 'email')
    list_editable = ('is_active',)
    inlines = [SalesRepTransactionInline]
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('name', 'phone'), ('email', 'user'), ('branch', 'address'))
        }),
        ('روابط الوصول والتطبيق', {
            'fields': ('display_app_link',),
            'description': 'استخدم هذا الرابط لإعطائه للمندوب ليتمكن من الدخول للتطبيق'
        }),
        ('نظام العمولات', {
            'fields': (('commission_type', 'commission_rate'),),
            'description': 'اختر نوع العمولة (نسبة أو مبلغ ثابت) ثم أدخل القيمة'
        }),
        ('الأداء (تُحدّث تلقائياً)', {
            'fields': (('total_sales', 'total_commission'),),
            'classes': ('collapse',)
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ('total_sales', 'total_commission', 'display_app_link')
    
    def display_app_link(self, obj):
        from core.models import SystemSettings
        from django.urls import reverse
        
        settings = SystemSettings.objects.first()
        base = settings.base_url if settings and settings.base_url else "http://127.0.0.1:8000"
        
        if base.endswith('/'): base = base[:-1]
        app_path = reverse('sales:mobile_app')
        full_url = f"{base}{app_path}"
        
        username = obj.user.username if obj.user else "---"
        
        return format_html(
            '<div style="background: rgba(212, 175, 55, 0.1); padding: 15px; border-radius: 12px; border: 1px solid var(--gold-primary);">'
            '<div style="margin-bottom: 10px;">'
            '<span style="color: #888; font-size: 12px;">اسم المستخدم للدخول:</span> '
            '<strong style="color: #fff; font-size: 16px; background: #333; padding: 2px 8px; border-radius: 4px;">{}</strong>'
            '</div>'
            '<div style="margin-bottom: 15px;">'
            '<span style="color: #888; font-size: 11px;">الرابط:</span> '
            '<code style="color: var(--gold-primary); font-size: 13px;">{}</code>'
            '</div>'
            '<a href="{}" target="_blank" style="background: var(--gold-primary); color: #000; padding: 8px 20px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">'
            'فتح التطبيق <i class="fa-solid fa-external-link" style="margin-right: 5px;"></i>'
            '</a>'
            '</div>',
            username, full_url, full_url
        )
    display_app_link.short_description = "بيانات دخول التطبيق للمندوب"
    
    def commission_display(self, obj):
        if obj.commission_type == 'percentage':
            return f"{obj.commission_rate}%"
        return f"{obj.commission_rate} ج.م"
    commission_display.short_description = "العمولة"
    
    def total_sales_display(self, obj):
        return format_html('<span style="color: #4CAF50; font-weight: bold;">{} ج.م</span>', obj.total_sales)
    total_sales_display.short_description = "إجمالي المبيعات"
    
    def total_commission_display(self, obj):
        return format_html('<span style="color: var(--gold-primary); font-weight: bold;">{} ج.م</span>', obj.total_commission)
    total_commission_display.short_description = "إجمالي العمولات"
    
    def status_badge(self, obj):
        from decimal import Decimal
        from django.utils.safestring import mark_safe
        
        # Handle case where no commission exists
        total_comm = obj.total_commission or Decimal('0')
        
        if total_comm <= 0:
            return mark_safe(
                '<span style="background: #607d8b; color: #fff; padding: 5px 15px; border-radius: 20px; font-size: 11px;">لا يوجد عمولات</span>'
            )
        
        # Calculate paid amount
        paid = obj.transactions.filter(transaction_type='payment').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        unpaid = total_comm - paid
        
        if unpaid <= 0:
            # Fully paid
            return mark_safe(
                '<span style="background: #4CAF50; color: #fff; padding: 5px 15px; border-radius: 20px; font-size: 11px;">✅ تم الصرف</span>'
            )
        elif paid > 0:
            # Partially paid
            return format_html(
                '<span style="background: #2196F3; color: #fff; padding: 5px 15px; border-radius: 20px; font-size: 11px; white-space: nowrap;">جزئي: {} ج.م</span>',
                round(unpaid, 2)
            )
        else:
            # Unpaid
            return format_html(
                '<span style="background: #ff9800; color: #000; padding: 5px 15px; border-radius: 20px; font-size: 11px; white-space: nowrap;">مستحق: {} ج.م</span>',
                round(unpaid, 2)
            )
    status_badge.short_description = "حالة المستحقات"


@admin.register(SalesRepTransaction)
class SalesRepTransactionAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('sales_rep', 'transaction_type', 'amount_display', 'invoice', 'created_at')
    list_filter = ('transaction_type', 'sales_rep', 'created_at')
    search_fields = ('sales_rep__name', 'invoice__invoice_number', 'notes')
    date_hierarchy = 'created_at'
    
    def amount_display(self, obj):
        color = '#4CAF50' if obj.transaction_type in ['commission', 'bonus'] else '#f44336'
        sign = '+' if obj.transaction_type in ['commission', 'bonus'] else '-'
        return format_html('<span style="color: {}; font-weight: bold;">{}{}</span>', color, sign, obj.amount)
    amount_display.short_description = "المبلغ"

