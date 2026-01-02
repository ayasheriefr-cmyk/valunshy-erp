"""
إدارة الخزينة والعهد - Admin
Treasury and Custody Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from django.urls import reverse
from django.utils.safestring import mark_safe
from .treasury_models import (
    Treasury, TreasuryTransaction, CustodyHolder, Custody, 
    CustodySettlement, ExpenseVoucher, ReceiptVoucher, 
    TreasuryTransfer, DailyTreasuryReport,
    TreasuryTool, ToolTransfer, CustodyTool, TreasuryType
)
from core.admin_mixins import ExportImportMixin


class TreasuryTransactionInline(admin.TabularInline):
    model = TreasuryTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'cash_amount', 'gold_weight', 'gold_carat', 
                       'description', 'date', 'balance_after_cash', 'created_by')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False


class TreasuryToolInline(admin.TabularInline):
    model = TreasuryTool
    extra = 1

@admin.register(TreasuryType)
class TreasuryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'color_badge', 'description')
    search_fields = ('name', 'code')
    prepopulated_fields = {'code': ('name',)}
    
    def color_badge(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 50%; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_badge.short_description = "اللون"

@admin.register(Treasury)
class TreasuryAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'treasury_type_badge', 'cash_balance_display', 
                    'gold_summary', 'responsible_user', 'is_active')
    list_filter = ('treasury_type', 'parent', 'is_active', 'branch')
    search_fields = ('code', 'name')
    list_editable = ('is_active',)
    inlines = [TreasuryTransactionInline, TreasuryToolInline]
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('code', 'name'), ('parent', 'treasury_type'), ('branch', 'responsible_user'))
        }),
        ('الأرصدة الحالية', {
            'fields': (
                'cash_balance',
                ('gold_balance_18', 'gold_balance_21', 'gold_balance_24'),
                ('gold_casting_balance', 'stones_balance'),
            ),
            'description': 'هذه الأرصدة تُحدّث تلقائياً من الحركات'
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ('cash_balance', 'gold_balance_18', 'gold_balance_21', 'gold_balance_24',
                       'gold_casting_balance', 'stones_balance')
    
    def treasury_type_badge(self, obj):
        if not obj.treasury_type:
            return "-"
        color = obj.treasury_type.color
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; '
            'font-size:12px; font-weight:bold;">{}</span>',
            color, color, obj.treasury_type.name
        )
    treasury_type_badge.short_description = 'النوع'
    
    def cash_balance_display(self, obj):
        color = '#4CAF50' if obj.cash_balance >= 0 else '#f44336'
        formatted_balance = '{:,.2f}'.format(float(obj.cash_balance))
        return format_html(
            '<span style="color:{}; font-weight:bold; font-size:14px;">{} ج.م</span>',
            color, formatted_balance
        )
    cash_balance_display.short_description = 'رصيد النقدية'
    
    def gold_summary(self, obj):
        return format_html(
            '<div style="font-size:12px; line-height:1.5;">'
            '<span style="color:#D4AF37;">18:</span> {} | '
            '<span style="color:#D4AF37;">21:</span> {} | '
            '<span style="color:#D4AF37;">24:</span> {}<br>'
            '<span style="color:#e91e63;">سبك:</span> {} | '
            '<span style="color:#9c27b0;">أحجار:</span> {}</div>',
            obj.gold_balance_18, obj.gold_balance_21, obj.gold_balance_24,
            obj.gold_casting_balance, obj.stones_balance
        )
    gold_summary.short_description = 'الأرصدة (ذهب/أحجار)'


@admin.register(TreasuryTransaction)
class TreasuryTransactionAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('date', 'treasury', 'transaction_type_badge', 'amount_display', 
                    'cost_center', 'description_short', 'balance_after_cash', 'created_by')
    list_filter = ('transaction_type', 'treasury', 'date', 'cost_center')
    search_fields = ('description', 'reference_type')
    date_hierarchy = 'date'
    readonly_fields = ('balance_after_cash', 'balance_after_gold', 'balance_after_gold_casting', 
                       'balance_after_stones', 'cost_center', 'created_by', 'created_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def transaction_type_badge(self, obj):
        colors = {
            'cash_in': '#4CAF50',
            'cash_out': '#f44336',
            'gold_in': '#D4AF37',
            'gold_out': '#FF9800',
            'transfer_in': '#2196F3',
            'transfer_out': '#9C27B0',
            'adjustment': '#607D8B',
        }
        color = colors.get(obj.transaction_type, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; '
            'font-size:11px; font-weight:bold;">{}</span>',
            color, color, obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = 'نوع الحركة'
    
    def amount_display(self, obj):
        parts = []
        if obj.cash_amount:
            color = '#4CAF50' if obj.transaction_type in ['cash_in', 'transfer_in'] else '#f44336'
            sign = '+' if obj.transaction_type in ['cash_in', 'transfer_in'] else '-'
            formatted = '{:,.2f}'.format(float(obj.cash_amount))
            parts.append('<span style="color:{};">{}{} ج.م</span>'.format(color, sign, formatted))
        if obj.gold_weight:
            color = '#D4AF37'
            sign = '+' if obj.transaction_type in ['gold_in', 'transfer_in'] else '-'
            parts.append('<span style="color:{};">{}{} جرام</span>'.format(color, sign, obj.gold_weight))
        if obj.gold_casting_weight:
            color = '#e91e63'
            sign = '+' if obj.transaction_type in ['gold_in', 'transfer_in'] else '-'
            parts.append('<span style="color:{};">{}{} جرام سبك</span>'.format(color, sign, obj.gold_casting_weight))
        if obj.stones_weight:
            color = '#9c27b0'
            sign = '+' if obj.transaction_type in ['gold_in', 'transfer_in'] else '-'
            parts.append('<span style="color:{};">{}{} قيراط أحجار</span>'.format(color, sign, obj.stones_weight))
        return mark_safe('<br>'.join(parts) if parts else '-')
    amount_display.short_description = 'المبلغ'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'البيان'


class CustodySettlementInline(admin.TabularInline):
    model = CustodySettlement
    extra = 0
    fields = ('settlement_type', 'cash_amount', 'gold_weight', 'gold_carat', 'reference', 'date', 'notes')

class CustodyToolInline(admin.TabularInline):
    model = CustodyTool
    extra = 1


@admin.register(CustodyHolder)
class CustodyHolderAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('user', 'holder_type_badge', 'current_cash_display', 'current_gold_display', 
                    'limits_display', 'is_active')
    list_filter = ('holder_type', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('بيانات المستلم', {
            'fields': ('user', 'holder_type', 'is_active')
        }),
        ('حدود العهدة', {
            'fields': (('max_cash_custody', 'max_gold_custody'),),
            'description': 'الحد الأقصى للعهدة المسموح بها'
        }),
        ('الأرصدة الحالية (للقراءة فقط)', {
            'fields': (
                'current_cash_custody',
                ('current_gold_18', 'current_gold_21', 'current_gold_24'),
            ),
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('current_cash_custody', 'current_gold_18', 'current_gold_21', 'current_gold_24')
    
    def holder_type_badge(self, obj):
        colors = {
            'employee': '#2196F3',
            'sales_rep': '#4CAF50',
            'workshop': '#FF9800',
            'technician': '#9C27B0',
        }
        color = colors.get(obj.holder_type, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; '
            'font-size:11px; font-weight:bold;">{}</span>',
            color, color, obj.get_holder_type_display()
        )
    holder_type_badge.short_description = 'النوع'
    
    def current_cash_display(self, obj):
        percent = (float(obj.current_cash_custody) / float(obj.max_cash_custody) * 100) if obj.max_cash_custody > 0 else 0
        color = '#4CAF50' if percent < 80 else '#FF9800' if percent < 100 else '#f44336'
        formatted = '{:,.2f}'.format(float(obj.current_cash_custody))
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} ج.م</span>',
            color, formatted
        )
    current_cash_display.short_description = 'العهدة النقدية'
    
    def current_gold_display(self, obj):
        total = obj.total_gold_custody
        return format_html('<span style="color:#D4AF37; font-weight:bold;">{} جرام</span>', total)
    current_gold_display.short_description = 'عهدة الذهب'
    
    def limits_display(self, obj):
        formatted_cash = '{:,.0f}'.format(float(obj.max_cash_custody))
        return format_html(
            '<div style="font-size:11px;">'
            'نقد: {} | ذهب: {} جرام</div>',
            formatted_cash, obj.max_gold_custody
        )
    limits_display.short_description = 'الحدود'


@admin.register(Custody)
class CustodyAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('custody_number', 'holder', 'custody_type_badge', 'amounts_display', 
                    'remaining_display', 'status_badge', 'issue_date', 'due_date_display')
    list_filter = ('status', 'custody_type', 'treasury', 'issue_date')
    search_fields = ('custody_number', 'holder__user__username', 'purpose')
    date_hierarchy = 'issue_date'
    inlines = [CustodySettlementInline, CustodyToolInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, 'created_by') and not instance.created_by_id:
                instance.created_by = request.user
            instance.save()
        formset.save_m2m()
    
    fieldsets = (
        ('بيانات السند', {
            'fields': (('custody_number', 'custody_type'), ('treasury', 'holder'), 'status')
        }),
        ('المبالغ', {
            'fields': (
                'cash_amount',
                ('gold_weight_18', 'gold_weight_21', 'gold_weight_24'),
            )
        }),
        ('المسدد', {
            'fields': (
                'settled_cash',
                ('settled_gold_18', 'settled_gold_21', 'settled_gold_24'),
            ),
            'classes': ('collapse',)
        }),
        ('التفاصيل', {
            'fields': ('purpose', ('issue_date', 'due_date'))
        }),
        ('الاعتماد', {
            'fields': ('approved_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('custody_number', 'settled_cash', 'settled_gold_18', 'settled_gold_21', 'settled_gold_24')
    
    def custody_type_badge(self, obj):
        colors = {'cash': '#4CAF50', 'gold': '#D4AF37', 'mixed': '#2196F3'}
        color = colors.get(obj.custody_type, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 10px; border-radius:12px; '
            'font-size:11px;">{}</span>',
            color, color, obj.get_custody_type_display()
        )
    custody_type_badge.short_description = 'النوع'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FF9800',
            'active': '#2196F3',
            'partial_settled': '#9C27B0',
            'settled': '#4CAF50',
            'cancelled': '#f44336',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:15px; '
            'font-size:11px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'
    
    def amounts_display(self, obj):
        parts = []
        if obj.cash_amount:
            formatted = '{:,.2f}'.format(float(obj.cash_amount))
            parts.append('<span style="color:#4CAF50;">{} ج.م</span>'.format(formatted))
        if obj.total_gold:
            parts.append('<span style="color:#D4AF37;">{} جرام</span>'.format(obj.total_gold))
        return format_html('<br>'.join(parts) if parts else '-')
    amounts_display.short_description = 'قيمة العهدة'
    
    def remaining_display(self, obj):
        parts = []
        if obj.remaining_cash > 0:
            formatted = '{:,.2f}'.format(float(obj.remaining_cash))
            parts.append('<span style="color:#f44336;">{} ج.م</span>'.format(formatted))
        if obj.remaining_gold > 0:
            parts.append('<span style="color:#FF9800;">{} جرام</span>'.format(obj.remaining_gold))
        if not parts:
            return mark_safe('<span style="color:#4CAF50;">مسدد ✓</span>')
        return mark_safe('<br>'.join(parts))
    remaining_display.short_description = 'المتبقي'
    
    def due_date_display(self, obj):
        if not obj.due_date:
            return '-'
        if obj.is_overdue:
            return format_html(
                '<span style="background:#f4433622; color:#f44336; padding:3px 8px; border-radius:10px;">'
                '⚠️ {}</span>',
                obj.due_date
            )
        return obj.due_date
    due_date_display.short_description = 'الاستحقاق'


@admin.register(ExpenseVoucher)
class ExpenseVoucherAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('voucher_number', 'voucher_type_badge', 'beneficiary_name', 'amount_display',
                    'expense_category', 'cost_center', 'status_badge', 'date', 'treasury')
    list_filter = ('status', 'voucher_type', 'expense_category', 'cost_center', 'treasury', 'date')
    search_fields = ('voucher_number', 'beneficiary_name', 'description')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('بيانات الإذن', {
            'fields': (('voucher_number', 'voucher_type'), ('status', 'treasury'))
        }),
        ('المستفيد', {
            'fields': (('beneficiary_name', 'beneficiary_id'),)
        }),
        ('التفاصيل المالية', {
            'fields': (('amount', 'expense_category'), 'cost_center', 'description')
        }),
        ('التواريخ', {
            'fields': (('date', 'paid_date'),)
        }),
        ('الاعتمادات', {
            'fields': ('requested_by', 'approved_by', 'paid_by'),
            'classes': ('collapse',)
        }),
        ('المرفقات', {
            'fields': ('attachment',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('voucher_number',)
    
    def voucher_type_badge(self, obj):
        colors = {
            'expense': '#f44336',
            'advance': '#FF9800',
            'refund': '#4CAF50',
            'salary': '#2196F3',
            'bonus': '#9C27B0',
        }
        color = colors.get(obj.voucher_type, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 10px; border-radius:12px; '
            'font-size:11px;">{}</span>',
            color, color, obj.get_voucher_type_display()
        )
    voucher_type_badge.short_description = 'النوع'
    
    def amount_display(self, obj):
        formatted = '{:,.2f}'.format(float(obj.amount))
        return format_html(
            '<span style="color:#f44336; font-weight:bold; font-size:14px;">{} ج.م</span>',
            formatted
        )
    amount_display.short_description = 'المبلغ'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#9E9E9E',
            'pending': '#FF9800',
            'approved': '#2196F3',
            'paid': '#4CAF50',
            'rejected': '#f44336',
            'cancelled': '#607D8B',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:15px; '
            'font-size:11px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'


@admin.register(ReceiptVoucher)
class ReceiptVoucherAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('voucher_number', 'voucher_type_badge', 'payer_name', 'amounts_display',
                    'cost_center', 'status_badge', 'date', 'treasury')
    list_filter = ('status', 'voucher_type', 'payment_method', 'cost_center', 'treasury', 'date')
    search_fields = ('voucher_number', 'payer_name', 'description')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('بيانات الإذن', {
            'fields': (('voucher_number', 'voucher_type'), ('status', 'treasury'))
        }),
        ('الدافع', {
            'fields': ('payer_name', 'payment_method')
        }),
        ('المبالغ', {
            'fields': (('cash_amount', 'gold_weight', 'gold_carat'),)
        }),
        ('التفاصيل', {
            'fields': ('cost_center', 'description', 'date')
        }),
        ('الاستلام', {
            'fields': ('received_by',)
        }),
    )
    
    readonly_fields = ('voucher_number',)
    
    def voucher_type_badge(self, obj):
        color = '#4CAF50'
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 10px; border-radius:12px; '
            'font-size:11px;">{}</span>',
            color, color, obj.get_voucher_type_display()
        )
    voucher_type_badge.short_description = 'النوع'
    
    def amounts_display(self, obj):
        parts = []
        if obj.cash_amount:
            formatted = '{:,.2f}'.format(float(obj.cash_amount))
            parts.append('<span style="color:#4CAF50; font-weight:bold;">{} ج.م</span>'.format(formatted))
        if obj.gold_weight:
            parts.append('<span style="color:#D4AF37;">{} جرام</span>'.format(obj.gold_weight))
        return format_html('<br>'.join(parts) if parts else '-')
    amounts_display.short_description = 'المبلغ'
    
    def status_badge(self, obj):
        colors = {'draft': '#FF9800', 'confirmed': '#4CAF50', 'cancelled': '#607D8B'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:15px; '
            'font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'


@admin.register(TreasuryTransfer)
class TreasuryTransferAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('transfer_number', 'from_treasury', 'to_treasury', 'amounts_display',
                    'cost_center', 'status_badge', 'date', 'initiated_by')
    list_filter = ('status', 'from_treasury', 'to_treasury', 'cost_center', 'date')
    search_fields = ('transfer_number', 'notes')
    date_hierarchy = 'date'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.initiated_by = request.user
        super().save_model(request, obj, form, change)

    fieldsets = (
        ('بيانات التحويل', {
            'fields': ('transfer_number', ('from_treasury', 'to_treasury'), ('status', 'cost_center'))
        }),
        ('المبالغ', {
            'fields': (('cash_amount', 'gold_weight', 'gold_carat'),)
        }),
        ('التفاصيل', {
            'fields': ('notes', 'date')
        }),
        ('التأكيد', {
            'fields': (('initiated_by', 'confirmed_by'),)
        }),
    )
    
    readonly_fields = ('transfer_number',)
    
    def amounts_display(self, obj):
        parts = []
        if obj.cash_amount:
            formatted = '{:,.2f}'.format(float(obj.cash_amount))
            parts.append('{} ج.م'.format(formatted))
        if obj.gold_weight:
            parts.append('{} جرام ذهب'.format(obj.gold_weight))
        return ' + '.join(parts) if parts else '-'
    amounts_display.short_description = 'المبلغ'
    
    def status_badge(self, obj):
        colors = {'pending': '#FF9800', 'completed': '#4CAF50', 'cancelled': '#f44336'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:5px 12px; border-radius:15px; '
            'font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'


@admin.register(DailyTreasuryReport)
class DailyTreasuryReportAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('date', 'treasury', 'opening_cash', 'movements_summary', 'closing_cash',
                    'difference_display', 'is_closed')
    list_filter = ('treasury', 'is_closed', 'date')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('treasury', 'date'), 'is_closed')
        }),
        ('الأرصدة الافتتاحية', {
            'fields': (
                'opening_cash',
                ('opening_gold_18', 'opening_gold_21', 'opening_gold_24'),
                ('opening_gold_casting', 'opening_stones'),
            )
        }),
        ('الحركات', {
            'fields': (
                ('total_cash_in', 'total_cash_out'),
                ('total_gold_in', 'total_gold_out'),
            )
        }),
        ('الأرصدة الختامية', {
            'fields': (
                'closing_cash',
                ('closing_gold_18', 'closing_gold_21', 'closing_gold_24'),
                ('closing_gold_casting', 'closing_stones'),
            )
        }),
        ('الجرد الفعلي', {
            'fields': (
                'actual_cash',
                ('actual_gold_18', 'actual_gold_21', 'actual_gold_24'),
                ('actual_gold_casting', 'actual_stones'),
                ('cash_difference', 'gold_difference'),
                ('gold_casting_difference', 'stones_difference'),
            ),
            'classes': ('collapse',)
        }),
        ('ملاحظات', {
            'fields': ('notes', 'closed_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('cash_difference', 'gold_difference', 'gold_casting_difference', 'stones_difference')
    
    def movements_summary(self, obj):
        formatted_in = '{:,.0f}'.format(float(obj.total_cash_in))
        formatted_out = '{:,.0f}'.format(float(obj.total_cash_out))
        return format_html(
            '<span style="color:#4CAF50;">+{}</span> / '
            '<span style="color:#f44336;">-{}</span>',
            formatted_in, formatted_out
        )
    movements_summary.short_description = 'الحركات'
    
    def difference_display(self, obj):
        if (obj.cash_difference == 0 and obj.gold_difference == 0 and 
            obj.gold_casting_difference == 0 and obj.stones_difference == 0):
            return format_html('<span style="color:#4CAF50;">{}</span>', 'متطابق ✓')
        
        parts = []
        if obj.cash_difference != 0:
            color = '#f44336' if obj.cash_difference < 0 else '#FF9800'
            formatted = '{:+,.2f}'.format(float(obj.cash_difference))
            parts.append('<span style="color:{};">نقد: {}</span>'.format(color, formatted))
        if obj.gold_difference != 0:
            color = '#f44336' if obj.gold_difference < 0 else '#FF9800'
            formatted = '{:+,.3f}'.format(float(obj.gold_difference))
            parts.append('<span style="color:{};">ذهب: {}</span>'.format(color, formatted))
        if obj.gold_casting_difference != 0:
            color = '#f44336' if obj.gold_casting_difference < 0 else '#FF9800'
            formatted = '{:+,.3f}'.format(float(obj.gold_casting_difference))
            parts.append('<span style="color:{};">سبك: {}</span>'.format(color, formatted))
        if obj.stones_difference != 0:
            color = '#f44336' if obj.stones_difference < 0 else '#FF9800'
            formatted = '{:+,.3f}'.format(float(obj.stones_difference))
            parts.append('<span style="color:{};">أحجار: {}</span>'.format(color, formatted))
        return mark_safe('<br>'.join(parts)) if parts else '-'
    difference_display.short_description = 'الفروق'

@admin.register(ToolTransfer)
class ToolTransferAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('transfer_number', 'from_treasury', 'to_treasury', 'tool', 'quantity', 'weight', 'status', 'date')
    list_filter = ('status', 'from_treasury', 'to_treasury', 'tool')
    search_fields = ('transfer_number', 'notes')
    readonly_fields = ('initiated_by', 'confirmed_by', 'date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.initiated_by = request.user
        super().save_model(request, obj, form, change)
