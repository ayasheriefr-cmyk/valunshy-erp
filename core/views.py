from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
from django.db.models import Sum, Count, Q
from django.utils import timezone
from sales.models import Invoice
from inventory.models import Item, Branch
from manufacturing.models import ManufacturingOrder, Workshop, WorkshopSettlement
from core.models import GoldPrice, Notification
from finance.treasury_models import Treasury
import datetime

def home_dashboard(request):
    # 0. Redirect Sales Reps
    if request.user.is_authenticated and hasattr(request.user, 'salesrepresentative'):
        return redirect('sales_dashboard')

    # 1. Sales Statistics (Today)
    today = timezone.localtime(timezone.now()).date()
    
    invoices_today = Invoice.objects.filter(created_at__date=today)
    total_sales_today = invoices_today.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    
    # Calculate % increase (vs yesterday)
    yesterday = today - datetime.timedelta(days=1)
    sales_yesterday = Invoice.objects.filter(created_at__date=yesterday).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    
    if sales_yesterday > 0:
        sales_increase_pct = int(((total_sales_today - sales_yesterday) / sales_yesterday) * 100)
    else:
        sales_increase_pct = 100 if total_sales_today > 0 else 0

    # 2. Inventory Statistics
    # Total finished inventory weight (Available + Sold for total assets reporting, or just available?)
    from inventory.models import RawMaterial
    
    finished_weight = Item.objects.aggregate(Sum('net_gold_weight'))['net_gold_weight__sum'] or 0
    raw_material_weight = RawMaterial.objects.aggregate(Sum('current_weight'))['current_weight__sum'] or 0
    
    # Include Treasury Gold in Total System Weight
    treasury_gold = Treasury.objects.aggregate(
        g18=Sum('gold_balance_18'),
        g21=Sum('gold_balance_21'),
        g24=Sum('gold_balance_24'),
        casting=Sum('gold_casting_balance')
    )
    t_gold_weight = (treasury_gold['g18'] or 0) + (treasury_gold['g21'] or 0) + (treasury_gold['g24'] or 0) + (treasury_gold['casting'] or 0)

    # Total Weight Display (Includes Treasury Assets)
    total_inventory_weight = finished_weight + raw_material_weight + t_gold_weight
    
    recent_items = Item.objects.all().order_by('-id')[:5]

    # 3. Manufacturing Stats
    active_job_orders = ManufacturingOrder.objects.all().count() 
    
    # 4. Customer Stats
    from crm.models import Customer
    total_customers = Customer.objects.count()
    new_customers_today = Customer.objects.filter(created_at__date=today).count()

    # 5. Financial & Gold Prices (NEW)
    live_gold_prices = GoldPrice.objects.all().order_by('-updated_at')[:3]
    
    total_cash_in_vault = Treasury.objects.aggregate(Sum('cash_balance'))['cash_balance__sum'] or 0
    
    # Fallback price if none exist
    price_21 = GoldPrice.objects.filter(carat__name__icontains='21').first()
    benchmark_price = float(price_21.price_per_gram) if price_21 else 3850.0 
    
    # Inventory Value Calculation: EXCLUDE Treasury (Cash/Capital), ONLY Items + Raw Material (Stock for Sale)
    inventory_only_weight = finished_weight + raw_material_weight
    estimated_inventory_value = float(inventory_only_weight) * benchmark_price

    # 6. CHARTS DATA PREPARATION
    
    # A. Sales Trend (Last 7 Days)
    dates = []
    sales_values = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        dates.append(d.strftime('%Y-%m-%d')) # Label
        val = Invoice.objects.filter(created_at__date=d).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        sales_values.append(float(val))

    # B. Inventory Breakdown by Carat (Items + Treasury)
    inventory_data = Item.objects.all().values('carat__name').annotate(total_weight=Sum('net_gold_weight'))
    
    # Helper dict to merge Items + Treasury
    dist_map = {}
    
    # 1. Add Items
    for i in inventory_data:
        c_name = i['carat__name']
        w = float(i['total_weight'])
        dist_map[c_name] = dist_map.get(c_name, 0) + w
        
    # 2. Add Treasury (Using the `treasury_gold` aggregate calculated earlier)
    # Ensure keys match your Carat names in DB, typically "عيار 18", "عيار 21" or English. Assuming Arabic based on user language.
    # Note: If carats are English in DB (e.g. "21K"), these keys might need adjustment.
    # Given the previous context, we will add generic keys if they don't exist or map to likely names.
    if treasury_gold['g18'] and treasury_gold['g18'] > 0:
        dist_map['عيار 18'] = dist_map.get('عيار 18', 0) + float(treasury_gold['g18'])
        
    if treasury_gold['g21'] and treasury_gold['g21'] > 0:
        dist_map['عيار 21'] = dist_map.get('عيار 21', 0) + float(treasury_gold['g21'])
        
    if treasury_gold['g24'] and treasury_gold['g24'] > 0:
        dist_map['عيار 24'] = dist_map.get('عيار 24', 0) + float(treasury_gold['g24'])

    if treasury_gold['casting'] and treasury_gold['casting'] > 0:
         dist_map['ذهب كسر/سبك'] = dist_map.get('ذهب كسر/سبك', 0) + float(treasury_gold['casting'])

    carat_labels = list(dist_map.keys())
    carat_values = list(dist_map.values())
    
    # Calculate percentages for display
    inventory_breakdown = []
    _total_weight = sum(carat_values)
    if _total_weight > 0:
        for idx, val in enumerate(carat_values):
            pct = round((val / _total_weight) * 100, 1)
            inventory_breakdown.append({
                'carat': carat_labels[idx],
                'pct': pct
            })

    # C. Manufacturing Detailed Data
    active_orders = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled']).order_by('-start_date')[:10]
    workshops = Workshop.objects.all()
    recent_settlements = WorkshopSettlement.objects.order_by('-date')[:5]
    
    # Average Scrap (Last 10 completed)
    completed_orders = ManufacturingOrder.objects.filter(status='completed').order_by('-end_date')[:10]
    avg_scrap = 0
    if completed_orders.exists():
        total_scrap_pct = 0
        count = 0
        for order in completed_orders:
            if order.input_weight > 0:
                scrap_pct = (order.scrap_weight / order.input_weight) * 100
                total_scrap_pct += float(scrap_pct)
                count += 1
        if count > 0:
            avg_scrap = total_scrap_pct / count

    # Workshops Summaries
    total_workshop_gold_18 = float(workshops.aggregate(Sum('gold_balance_18'))['gold_balance_18__sum'] or 0)
    total_workshop_gold_21 = float(workshops.aggregate(Sum('gold_balance_21'))['gold_balance_21__sum'] or 0)
    total_workshop_gold_24 = float(workshops.aggregate(Sum('gold_balance_24'))['gold_balance_24__sum'] or 0)
    total_workshop_gold_combined = total_workshop_gold_18 + total_workshop_gold_21 + total_workshop_gold_24
    total_workshop_labor = float(workshops.aggregate(Sum('labor_balance'))['labor_balance__sum'] or 0)

    # Workshop Gold Intake (Last 7 Days)
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

    active_summary = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled']).aggregate(
        total_count=Count('id'),
        total_weight=Sum('input_weight')
    )

    context = {
        'total_sales_today': total_sales_today,
        'sales_increase_pct': sales_increase_pct,
        'total_inventory_weight': round(total_inventory_weight, 2),
        'active_job_orders': active_job_orders,
        'total_customers': total_customers,
        'new_customers_today': new_customers_today,
        'recent_items': recent_items,
        
        'live_gold_prices': live_gold_prices,
        'total_cash_in_vault': total_cash_in_vault,
        'estimated_inventory_value': estimated_inventory_value,
        'today_date': today,
        
        'chart_dates': dates,
        'chart_sales': sales_values,
        'chart_carat_labels': carat_labels,
        'chart_carat_values': carat_values,
        'workshop_gold_data': workshop_gold_data,
        
        'active_orders': active_orders,
        'workshops': workshops,
        'recent_settlements': recent_settlements,
        'avg_scrap': avg_scrap,
        
        'total_active_count': active_summary['total_count'] or 0,
        'total_active_weight': active_summary['total_weight'] or 0,
        
        'total_workshop_gold_18': total_workshop_gold_18,
        'total_workshop_gold_21': total_workshop_gold_21,
        'total_workshop_gold_24': total_workshop_gold_24,
        'total_workshop_gold_combined': total_workshop_gold_combined,
        'total_workshop_labor': total_workshop_labor,
        
        'inventory_breakdown': inventory_breakdown,
    }
    
    return render(request, 'dashboard.html', context)

def ai_assistant_query(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '').lower()
            
            from .ai_engine import ValunshyAI
            
            ai = ValunshyAI(request.user)
            response = ai.process_query(query)
                
            return JsonResponse({'response': response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_notifications(request):
    if not request.user.is_authenticated:
        return JsonResponse({'notifications': []})
        
    notifs = Notification.objects.filter(is_read=False)[:10]
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'level': n.level,
        'time': n.created_at.strftime("%H:%M")
    } for n in notifs]
    
    return JsonResponse({'notifications': data})

def mark_notification_read(request, notif_id):
    if request.method == 'POST':
        try:
           n = Notification.objects.get(id=notif_id)
           n.is_read = True
           n.save()
           return JsonResponse({'status': 'ok'})
        except:
           return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})
