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

@admin.register(Account)
class AccountAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'parent', 'balance', 'gold_balance')
    list_filter = ('account_type', 'parent')
    search_fields = ('code', 'name')
    ordering = ('code',)

@admin.register(JournalEntry)
class JournalEntryAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('reference', 'date', 'description', 'total_debit', 'total_credit', 'is_balanced')
    search_fields = ('reference', 'description')
    list_filter = ('date',)
    inlines = [LedgerEntryInline]
    date_hierarchy = 'date'
    
    def total_debit(self, obj):
        return sum(entry.debit for entry in obj.ledger_entries.all())
    total_debit.short_description = "إجمالي المدين"
    
    def total_credit(self, obj):
        return sum(entry.credit for entry in obj.ledger_entries.all())
    total_credit.short_description = "إجمالي الدائن"
    
    def is_balanced(self, obj):
        debit = sum(entry.debit for entry in obj.ledger_entries.all())
        credit = sum(entry.credit for entry in obj.ledger_entries.all())
        if debit == credit:
            return "✅ متوازن"
        return "❌ غير متوازن"
    is_balanced.short_description = "الحالة"

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
