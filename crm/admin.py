from django.contrib import admin
from .models import Customer, Supplier
from core.admin_mixins import ExportImportMixin

from django.utils.html import format_html

@admin.register(Customer)
class CustomerAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('name', 'phone', 'money_balance_display', 'gold_balance_list', 'total_purchases_value')
    search_fields = ('name', 'phone')
    
    fieldsets = (
        ('بيانات العميل', {
            'fields': (('name', 'phone'), ('email', 'vat_number'))
        }),
        ('الأرصدة الحالية', {
            'fields': (('money_balance', 'loyalty_points'), ('gold_balance_18', 'gold_balance_21', 'gold_balance_24')),
            'description': 'الأرصدة المالية والذهبية الحالية في ذمة العميل'
        }),
        ('تواريخ تهمنا', {
            'fields': (('birth_date', 'wedding_anniversary'),),
            'classes': ('collapse',)
        }),
    )

    def money_balance_display(self, obj):
        color = "green" if obj.money_balance >= 0 else "red"
        return format_html('<b style="color:{};">{} ج.م</b>', color, obj.money_balance)
    money_balance_display.short_description = "الرصيد النقدي"

    def gold_balance_list(self, obj):
        return format_html(
            '<div style="font-size:0.85rem;">'
            '21K: <b>{} جم</b><br>'
            '18K: <b>{} جم</b>'
            '</div>', 
            obj.gold_balance_21, obj.gold_balance_18
        )
    gold_balance_list.short_description = "أرصدة الذهب"

@admin.register(Supplier)
class SupplierAdmin(ExportImportMixin, admin.ModelAdmin):
    list_display = ('supplier_code', 'name', 'primary_carat', 'phone', 'address', 'money_balance_display', 'gold_balance_list')
    list_filter = ('supplier_type', 'primary_carat')
    search_fields = ('name', 'phone', 'contact_person', 'address')
    
    fieldsets = (
        ('بيانات المورد', {
            'fields': (('name', 'supplier_type'), ('phone', 'contact_person'), ('email', 'vat_number'), 'address', 'primary_carat')
        }),
        ('الأرصدة الحالية', {
            'fields': (('money_balance',), ('gold_balance_18', 'gold_balance_21', 'gold_balance_24')),
            'description': 'الأرصدة المالية والذهبية الحالية للمورد'
        }),
        ('إضافي', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def supplier_code(self, obj):
        return f"{obj.id:04d}"
    supplier_code.short_description = "كود المورد"

    def money_balance_display(self, obj):
        color = "green" if obj.money_balance >= 0 else "red"
        return format_html('<b style="color:{};">{} ج.م</b>', color, obj.money_balance)
    money_balance_display.short_description = "الرصيد النقدي"

    def gold_balance_list(self, obj):
        return format_html(
            '<div style="font-size:0.85rem;">'
            '21K: <b style="color:var(--gold-primary);">{} جم</b><br>'
            '18K: <b>{} جم</b>'
            '</div>', 
            obj.gold_balance_21, obj.gold_balance_18
        )
    gold_balance_list.short_description = "أرصدة الذهب"
