from django.shortcuts import render
from django.db.models import Count, Avg, Sum, F
from django.db.models.functions import TruncDate
from django.utils import timezone
import datetime
import json
from .models import ManufacturingOrder, Workshop

def manufacturing_analytics(request):
    """
    Dedicated Manufacturing Analytics Dashboard
    """
    # 1. Pipeline Status (Orders per Stage)
    # Group by status
    pipeline_data = ManufacturingOrder.objects.exclude(status='cancelled').values('status').annotate(count=Count('id'))
    
    # Map status codes to labels
    status_map = dict(ManufacturingOrder.status_choices)
    pipeline_labels = [status_map.get(item['status'], item['status']) for item in pipeline_data]
    pipeline_values = [item['count'] for item in pipeline_data]

    # 2. Workshop Performance (Scrap Rate Analysis)
    # Calculate avg scrap percentage per workshop for completed orders
    workshop_stats = ManufacturingOrder.objects.filter(status='completed', input_weight__gt=0).values('workshop__name').annotate(
        avg_scrap_pct=Avg((F('scrap_weight') / F('input_weight')) * 100),
        total_produced=Sum('output_weight'),
        order_count=Count('id')
    ).order_by('avg_scrap_pct') # Best first

    ws_labels = [item['workshop__name'] for item in workshop_stats]
    ws_scrap_values = [round(item['avg_scrap_pct'] or 0, 2) for item in workshop_stats]
    ws_production_values = [float(item['total_produced'] or 0) for item in workshop_stats]

    # 3. High Scrap Outliers (Orders > 1%)
    outliers = ManufacturingOrder.objects.filter(
        status='completed',
        input_weight__gt=0
    ).annotate(
        scrap_pct=(F('scrap_weight') / F('input_weight')) * 100
    ).filter(scrap_pct__gt=1.0).order_by('-scrap_pct')[:10]

    # 4. Weekly Production Output (Last 7 Days)
    today = timezone.now().date()
    seven_days_ago = today - datetime.timedelta(days=7)
    
    daily_output = ManufacturingOrder.objects.filter(
        status='completed', 
        end_date__gte=seven_days_ago
    ).annotate(date=TruncDate('end_date')).values('date').annotate(
        daily_weight=Sum('output_weight')
    ).order_by('date')
    
    output_dates = []
    output_values = []
    date_map = {item['date']: item['daily_weight'] for item in daily_output}
    
    for i in range(8):
        d = seven_days_ago + datetime.timedelta(days=i)
        output_dates.append(d.strftime('%Y-%m-%d'))
        output_values.append(float(date_map.get(d, 0)))

    context = {
        'pipeline_labels': pipeline_labels,
        'pipeline_values': pipeline_values,
        'ws_labels': ws_labels,
        'ws_scrap_values': ws_scrap_values,
        'ws_production_values': ws_production_values,
        'workshop_stats': workshop_stats,
        'outliers': outliers,
        'output_dates': output_dates,
        'output_values': output_values,
        'total_active': ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled']).count(),
        'total_workshops': Workshop.objects.count()
    }
    
    return render(request, 'manufacturing/analytics.html', context)
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Avg, Count, F
from .models import Workshop, ManufacturingOrder, WorkshopSettlement, Stone

@staff_member_required
def manufacturing_dashboard(request):
    # 1. Workshop Summaries (Inventory Gold Balances)
    workshops = Workshop.objects.all()
    # Explicitly cast to float for template compatibility
    total_workshop_gold_18 = float(workshops.aggregate(Sum('gold_balance_18'))['gold_balance_18__sum'] or 0)
    total_workshop_gold_21 = float(workshops.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0)
    total_workshop_gold_24 = float(workshops.aggregate(Sum('gold_balance_24'))['gold_balance_24__sum'] or 0)
    total_workshop_gold_combined = total_workshop_gold_18 + total_workshop_gold_21 + total_workshop_gold_24
    total_workshop_labor = float(workshops.aggregate(Sum('labor_balance'))['labor_balance__sum'] or 0)




    # 2. Active Orders Tracking
    active_orders = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled']).order_by('-start_date')
    active_summary = active_orders.aggregate(
        total_count=Count('id'),
        total_weight=Sum('input_weight')
    )
    
    # 3. Efficiency & Scrap Analysis (Completed Projects)
    completed_orders = ManufacturingOrder.objects.filter(status='completed').order_by('-end_date')[:10]
    
    # Calculate average scrap percentage
    avg_scrap = 0
    if completed_orders.exists():
        scrap_stats = completed_orders.aggregate(
            total_in=Sum('input_weight'),
            total_scrap=Sum('scrap_weight')
        )
        if scrap_stats['total_in'] > 0:
            avg_scrap = (scrap_stats['total_scrap'] / scrap_stats['total_in']) * 100

    # 4. Recent Settlements (Daily Movements)
    recent_settlements = WorkshopSettlement.objects.all().order_by('-date')[:15]

    # 5. CHARTS DATA (Sales Trend & Inventory) - Added for Interactivity
    from sales.models import Invoice
    from inventory.models import Item
    
    # A. Sales Trend (Last 7 Days)
    dates = []
    sales_values = []
    today = timezone.now().date()
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        dates.append(d.strftime('%Y-%m-%d'))
        val = Invoice.objects.filter(created_at__date=d).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        sales_values.append(float(val))

    # B. Workshop Gold Intake (Last 7 Days)
    workshop_gold_data = []
    for ws in workshops:
        ws_daily_weights = []
        for i in range(6, -1, -1):
            d = today - datetime.timedelta(days=i)
            w = WorkshopSettlement.objects.filter(workshop=ws, settlement_type='gold_payment', date=d).aggregate(Sum('weight'))['weight__sum'] or 0
            ws_daily_weights.append(float(w))
        workshop_gold_data.append({
            'name': ws.name,
            'data': ws_daily_weights
        })

    # C. Inventory Breakdown
    # C. Inventory Breakdown (Cleaned & Grouped)
    inventory_raw = Item.objects.filter(status='available').values('carat__name').annotate(total_weight=Sum('net_gold_weight'))
    carat_groups = {}
    for item in inventory_raw:
        raw_name = item['carat__name'] or "غير محدد"
        # Normalize: "18K", "18k", "18 " -> "18K"
        clean_name = raw_name.upper().replace('K', '').strip() + 'K'
        if clean_name not in carat_groups:
            carat_groups[clean_name] = 0
        carat_groups[clean_name] += float(item['total_weight'] or 0)
    
    carat_labels = list(carat_groups.keys())
    carat_values = list(carat_groups.values())

    # D. Stone Inventory Alert & Status (Diamond Focus)
    from django.db.models import DecimalField, ExpressionWrapper
    stones = Stone.objects.all()
    total_stone_carats = 0
    stone_details = []
    
    for stone in stones:
        stock = float(stone.current_stock or 0)
        unit = str(stone.unit).lower()
        
        # Normalize to Carats (1 gram = 5 carats)
        ct_weight = stock
        if 'gram' in unit or 'جم' in unit:
            ct_weight = stock * 5
        
        total_stone_carats += ct_weight
        if stock > 0:
            stone_details.append({
                'name': stone.name,
                'stock': stock,
                'unit': stone.get_unit_display() if hasattr(stone, 'get_unit_display') else unit,
                'carats': ct_weight
            })
    
    # Alert Level Logic
    stone_alert_level = 'safe'
    if total_stone_carats >= 150:
        stone_alert_level = 'critical'
    elif total_stone_carats >= 140:
        stone_alert_level = 'warning'

    context = {
        'title': 'لوحة تحكم الإنتاج والجرد',
        'workshops': workshops,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'avg_scrap': avg_scrap,
        'recent_settlements': recent_settlements,
        
        # Summary Stats (Gold & Labor)
        'total_workshop_gold_18': total_workshop_gold_18,
        'total_workshop_gold_21': total_workshop_gold_21,
        'total_workshop_gold_24': total_workshop_gold_24,
        'total_workshop_gold_combined': total_workshop_gold_combined,
        'total_workshop_labor': total_workshop_labor,
        
        'total_active_count': active_summary['total_count'] or 0,
        'total_active_weight': active_summary['total_weight'] or 0,

        # Stone Inventory
        'total_stone_carats': total_stone_carats,
        'stone_details': stone_details,
        'stone_alert_level': stone_alert_level,

        # Charts Data
        'chart_dates': dates,
        'chart_sales': sales_values,
        'chart_carat_labels': carat_labels,
        'chart_carat_values': carat_values,
        'workshop_gold_data': workshop_gold_data,
    }


    return render(request, 'manufacturing/dashboard.html', context)

@staff_member_required
def print_job_card(request, order_id):
    """طباعة بطاقة الشغل (Job Card) للصنايعي مع باركود"""
    order = ManufacturingOrder.objects.get(id=order_id)
    return render(request, 'manufacturing/job_card.html', {'order': order})
