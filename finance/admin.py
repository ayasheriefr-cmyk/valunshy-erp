from django.contrib import admin
from .models import Account, JournalEntry, LedgerEntry, FinanceSettings, FiscalYear, OpeningBalance, CostCenter
# Import treasury admin to register all treasury models
from . import treasury_admin
from core.admin_mixins import ExportImportMixin

class LedgerEntryInline(admin.TabularInline):
    model = LedgerEntry
    extra = 2
    fields = ('account', 'cost_center', 'debit', 'credit', 'gold_debit', 'gold_credit')
    classes = ('finance-inline',)
    verbose_name = "بند القيد"
    verbose_name_plural = "بنود القيد"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('account', 'cost_center')

@admin.register(Account)
class AccountAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'parent', 'balance', 'gold_balance')
    list_filter = ('account_type', 'parent')
    search_fields = ('code', 'name')
    ordering = ('code',)

@admin.register(JournalEntry)
class JournalEntryAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('reference', 'date', 'description_short', 'total_debit', 'total_credit', 'is_balanced', 'entry_count')
    search_fields = ('reference', 'description')
    list_filter = ('date',)
    inlines = [LedgerEntryInline]
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'total_debit_display', 'total_credit_display', 'balance_status')
    
    fieldsets = (
        ('معلومات القيد', {
            'fields': ('reference', 'date', 'description')
        }),
        ('ملخص القيد', {
            'fields': ('total_debit_display', 'total_credit_display', 'balance_status'),
            'classes': ('collapse',),
            'description': 'ملخص تلقائي لإجماليات القيد'
        }),
    )
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
        return '-'
    description_short.short_description = "الوصف"
    
    def total_debit(self, obj):
        total = sum(entry.debit for entry in obj.ledger_entries.all())
        return f"{total:,.2f}"
    total_debit.short_description = "إجمالي المدين"
    
    def total_credit(self, obj):
        total = sum(entry.credit for entry in obj.ledger_entries.all())
        return f"{total:,.2f}"
    total_credit.short_description = "إجمالي الدائن"
    
    def total_debit_display(self, obj):
        from django.utils.html import format_html
        total = sum(entry.debit for entry in obj.ledger_entries.all())
        return format_html('<b style="color:#e74c3c;">{:,.2f} جنيه</b>', total)
    total_debit_display.short_description = "إجمالي المدين"
    
    def total_credit_display(self, obj):
        from django.utils.html import format_html
        total = sum(entry.credit for entry in obj.ledger_entries.all())
        return format_html('<b style="color:#27ae60;">{:,.2f} جنيه</b>', total)
    total_credit_display.short_description = "إجمالي الدائن"
    
    def balance_status(self, obj):
        from django.utils.html import format_html
        debit = sum(entry.debit for entry in obj.ledger_entries.all())
        credit = sum(entry.credit for entry in obj.ledger_entries.all())
        if debit == credit:
            return format_html('<span style="color:#27ae60; font-weight:bold;">✅ متوازن</span>')
        diff = abs(debit - credit)
        return format_html('<span style="color:#e74c3c; font-weight:bold;">❌ غير متوازن (فرق: {:,.2f})</span>', diff)
    balance_status.short_description = "حالة التوازن"
    
    def is_balanced(self, obj):
        debit = sum(entry.debit for entry in obj.ledger_entries.all())
        credit = sum(entry.credit for entry in obj.ledger_entries.all())
        if debit == credit:
            return "✅ متوازن"
        return "❌ غير متوازن"
    is_balanced.short_description = "الحالة"
    
    def entry_count(self, obj):
        return obj.ledger_entries.count()
    entry_count.short_description = "عدد البنود"

@admin.register(FinanceSettings)
class FinanceSettingsAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('id', 'cash_account', 'sales_revenue_account', 'inventory_gold_account')
    
    def has_add_permission(self, request):
        return not FinanceSettings.objects.exists()

@admin.register(FiscalYear)
class FiscalYearAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'is_closed')
    list_filter = ('is_active', 'is_closed')
    list_editable = ('is_active',)
    


@admin.register(OpeningBalance)
class OpeningBalanceAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('fiscal_year', 'account', 'debit_balance', 'credit_balance', 'gold_balance')
    list_filter = ('fiscal_year', 'account__account_type')
    search_fields = ('account__name', 'account__code')

@admin.register(CostCenter)
class CostCenterAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('code',)
