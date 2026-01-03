from django.contrib import admin
from django.db.models import Sum
from decimal import Decimal


@admin.register(CostAllocation)
class CostAllocationAdmin(admin.ModelAdmin):
    list_display = ('period_name', 'start_date', 'end_date', 'total_overhead_display', 'allocation_basis', 'status_badge', 'orders_count')
    list_filter = ('status', 'allocation_basis')
    search_fields = ('period_name',)
    readonly_fields = ('total_production_weight_snapshot', 'total_labor_cost_snapshot', 'created_at', 'updated_at')
    
    fieldsets = (
        ('الفترة الزمنية', {
            'fields': (('period_name',), ('start_date', 'end_date'))
        }),
        ('إجمالي التكاليف', {
            'fields': (
                ('total_electricity', 'total_water'),
                ('total_gas', 'total_rent'),
                ('total_salaries', 'total_other'),
            )
        }),
        ('إعدادات التوزيع', {
            'fields': (('allocation_basis', 'status'),)
        }),
        ('إحصائيات (بعد التطبيق)', {
            'fields': (('total_production_weight_snapshot', 'total_labor_cost_snapshot'),),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['apply_cost_allocation']
    
    def total_overhead_display(self, obj):
        from django.utils.html import format_html
        val = float(obj.total_overhead_amount or 0)
        return format_html('<span style="color:#4CAF50; font-weight:bold;">{} ج.م</span>', f"{val:,.2f}")
    total_overhead_display.short_description = 'إجمالي التكاليف'
    
    def status_badge(self, obj):
        from django.utils.html import format_html
        colors = {
            'draft': '#FF9800',
            'applied': '#4CAF50',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{}22; color:{}; padding:4px 12px; border-radius:15px; font-weight:bold;">{}</span>',
            color, color, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'
    
    def orders_count(self, obj):
        from django.utils.html import format_html
        from .models import ManufacturingOrder
        count = ManufacturingOrder.objects.filter(cost_allocation=obj).count()
        return format_html('<span style="font-weight:bold;">{}</span>', count)
    orders_count.short_description = 'عدد الأوامر المرتبطة'
    
    def apply_cost_allocation(self, request, queryset):
        from django.contrib import messages
        from .models import ManufacturingOrder
        
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
            
            # Save snapshots
            cost_allocation.total_production_weight_snapshot = orders.aggregate(total=Sum('output_weight'))['total'] or Decimal('0')
            cost_allocation.total_labor_cost_snapshot = orders.aggregate(total=Sum('manufacturing_pay'))['total'] or Decimal('0')
            
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
            
            # Mark as applied
            cost_allocation.status = 'applied'
            cost_allocation.save()
            
            messages.success(request, f'تم توزيع تكاليف "{cost_allocation.period_name}" على {orders.count()} أمر تصنيع.')
    
    apply_cost_allocation.short_description = 'احتساب وتطبيق التكاليف على الأوامر'
