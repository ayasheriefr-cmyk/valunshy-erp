from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Avg, Sum, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
import json
from .models import ManufacturingOrder, Workshop, Stone, InstallationTool, OrderStone, OrderTool, ProductionStage, WorkshopTransfer, WorkshopSettlement
from inventory.models import RawMaterial, Carat, Branch
from finance.treasury_models import Treasury, TreasuryTransaction

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




    # 2. Active Orders Tracking (Optimized with prefetch)
    active_orders = ManufacturingOrder.objects.exclude(
        status__in=['completed', 'cancelled']
    ).select_related('workshop', 'carat').prefetch_related('stages').order_by('-start_date')
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
    
    # A. Sales Trend (Last 7 Days) - Optimized
    today = timezone.now().date()
    start_date = today - datetime.timedelta(days=6)
    
    sales_trend_data = Invoice.objects.filter(
        created_at__date__gte=start_date
    ).extra(select={'day': "date(created_at)"}).values('day').annotate(total=Sum('grand_total'))
    
    # Map result to date string
    sales_map = {str(item['day']): float(item['total']) for item in sales_trend_data}
    
    dates = []
    sales_values = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        dates.append(d_str)
        # Handle potential different date formats from extra select
        val = sales_map.get(d_str, 0) or sales_map.get(str(d), 0)
        sales_values.append(val)

    # B. Workshop Gold Intake (Last 7 Days) - Optimized
    ws_intake_data = WorkshopSettlement.objects.filter(
        settlement_type='gold_payment',
        date__gte=start_date
    ).values('workshop_id', 'date').annotate(total_w=Sum('weight'))
    
    # Map: (workshop_id, date_str) -> weight
    intake_map = {}
    for item in ws_intake_data:
        key = (item['workshop_id'], str(item['date']))
        intake_map[key] = float(item['total_w'])
        
    workshop_gold_data = []
    for ws in workshops:
        ws_daily_weights = []
        for i in range(6, -1, -1):
            d = today - datetime.timedelta(days=i)
            weight = intake_map.get((ws.id, str(d)), 0)
            ws_daily_weights.append(weight)
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
    
    # Alert Level Logic (Vibrant UI Tokens)
    stone_alert_level = 'safe'
    stone_percentage = 0
    alert_bg = "rgba(255, 255, 255, 0.05)"
    alert_border = "rgba(255, 255, 255, 0.1)"
    alert_color = "#ccc"
    alert_title = ""
    
    if total_stone_carats > 0:
        stone_percentage = min((total_stone_carats / 150) * 100, 100)
        
    if total_stone_carats >= 150:
        stone_alert_level = 'critical'
        alert_bg = "rgba(255, 82, 82, 0.2)"
        alert_border = "#ff5252"
        alert_color = "#ff5252"
        alert_title = "تنبيه حرج جداً: رصيد الحجارة تجاوز الحد القانوني!"
    elif total_stone_carats >= 140:
        stone_alert_level = 'warning'
        alert_bg = "rgba(255, 152, 0, 0.2)"
        alert_border = "#ff9800"
        alert_color = "#ff9800"
        alert_title = "تنبيه: رصيد الحجارة يقترب من الحد الأقصى"

    # Calculate Difference from 150ct limit
    stone_diff = total_stone_carats - 150

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
        'stone_percentage': stone_percentage,
        'alert_bg': alert_bg,
        'alert_border': alert_border,
        'alert_color': alert_color,
        'alert_title': alert_title,
        'stone_diff': stone_diff,
        'stone_diff_abs': abs(stone_diff),

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

@staff_member_required
def fast_order_create(request):
    """شاشة إنشاء أمر تصنيع سريع (Wizard)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 1. Create Main Order
            order = ManufacturingOrder.objects.create(
                order_number=data.get('order_number'),
                workshop_id=data.get('workshop'),
                carat_id=data.get('carat'),
                input_material_id=data.get('input_material'),
                input_weight=data.get('input_weight'),
                status='in_progress', # Start directly in progress
                item_name_pattern=data.get('item_name'),
                target_branch_id=data.get('target_branch'),
                assigned_technician=data.get('technician', '')
            )
            
            # 2. Add Stones
            for stone_data in data.get('stones', []):
                if stone_data.get('id'):
                    OrderStone.objects.create(
                        order=order,
                        stone_id=stone_data['id'],
                        quantity_issued=stone_data['qty'],
                        quantity_required=stone_data['qty']
                    )
            
            # 3. Add Tools/Materials (Solder/Laser wire)
            for tool_data in data.get('tools', []):
                if tool_data.get('id'):
                    OrderTool.objects.create(
                        order=order,
                        tool_id=tool_data['id'],
                        weight=tool_data.get('weight', 0),
                        quantity=tool_data.get('qty', 0)
                    )
            
            return JsonResponse({'status': 'success', 'order_id': order.id, 'redirect_url': f'/admin/manufacturing/manufacturingorder/{order.id}/change/'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # Context for GET request
    context = {
        'workshops': Workshop.objects.all(),
        'carats': Carat.objects.all(),
        'raw_materials': RawMaterial.objects.filter(current_weight__gt=0),
        'stones': Stone.objects.filter(current_stock__gt=0),
        'tools': InstallationTool.objects.all(),
        'branches': Branch.objects.all(),
        'next_order_number': f"MFG-{timezone.now().strftime('%Y%m%d')}-{ManufacturingOrder.objects.count() + 1}"
    }
    return render(request, 'manufacturing/fast_order.html', context)

@csrf_exempt
def magic_workflow(request):
    """
    Magic Manufacturing Workflow: Drag-and-Drop Production Management
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        order_id = request.POST.get('order_id')
        
        try:
            with transaction.atomic():
                if action == 'assign_workshop':
                    workshop_id = request.POST.get('workshop_id')
                    input_weight = request.POST.get('input_weight', 0)
                    treasury_id = request.POST.get('treasury_id')
                    
                    order = get_object_or_404(ManufacturingOrder, id=order_id)
                    workshop = get_object_or_404(Workshop, id=workshop_id)
                    
                    # 1. Update Order
                    order.workshop = workshop
                    order.status = 'in_progress'
                    if input_weight:
                        order.input_weight = input_weight
                    order.save()
                    
                    # 3. Material Issuance (Gold & Treasury Transaction)
                    gold_weight = request.POST.get('gold_weight')
                    if gold_weight and float(gold_weight) > 0:
                        # Create Workshop Settlement (Increases Workshop Debt)
                        WorkshopSettlement.objects.create(
                            workshop=workshop,
                            settlement_type='gold_payment',
                            weight=gold_weight,
                            carat=order.carat,
                            notes=f"صرف ذهب سريع مع الطلب {order.order_number}"
                        )
                        
                        # Create Treasury Transaction (Decreases Treasury Stock)
                        if treasury_id:
                            treasury = get_object_or_404(Treasury, id=treasury_id)
                            TreasuryTransaction.objects.create(
                                treasury=treasury,
                                transaction_type='gold_out',
                                gold_weight=gold_weight,
                                gold_carat=order.carat,
                                description=f"صرف ذهب لطلب تصنيع: {order.order_number} (للعامل: {workshop.name})",
                                reference_type='manufacturing_order',
                                reference_id=order.id,
                                created_by=request.user if request.user.is_authenticated else None
                            )
                    
                    # 4. Add Stones if provided
                    stones_json = request.POST.get('stones_json')
                    if stones_json:
                        import json
                        stones = json.loads(stones_json)
                        for s in stones:
                            OrderStone.objects.create(
                                order=order, 
                                stone_id=s['id'], 
                                quantity_issued=s['qty'], 
                                quantity_required=s['qty']
                            )

                    # 2. Create first stage
                    ProductionStage.objects.create(
                        order=order,
                        workshop=workshop,
                        stage_name='casting',
                        input_weight=input_weight or 0,
                        start_datetime=timezone.now()
                    )
                    
                    return JsonResponse({'status': 'success'})

                elif action == 'move_order':
                    next_workshop_id = request.POST.get('next_workshop_id')
                    output_weight = request.POST.get('output_weight', 0)
                    powder_weight = request.POST.get('powder_weight', 0)
                    
                    order = get_object_or_404(ManufacturingOrder, id=order_id)
                    next_workshop = get_object_or_404(Workshop, id=next_workshop_id)
                    
                    # Close current stage
                    current_stage = order.stages.filter(end_datetime__isnull=True).last()
                    if current_stage:
                        current_stage.output_weight = output_weight
                        current_stage.powder_weight = powder_weight
                        current_stage.next_workshop = next_workshop
                        current_stage.save() # Signal handles WorkshopTransfer
                        
                        # Create next stage
                        ProductionStage.objects.create(
                            order=order,
                            workshop=next_workshop,
                            stage_name='crafting',
                            input_weight=output_weight,
                            start_datetime=timezone.now()
                        )
                    
                    return JsonResponse({'status': 'success'})

                elif action == 'complete_order':
                    output_weight = request.POST.get('output_weight', 0)
                    powder_weight = request.POST.get('powder_weight', 0)
                    
                    order = get_object_or_404(ManufacturingOrder, id=order_id)
                    
                    # Close last stage
                    current_stage = order.stages.filter(end_datetime__isnull=True).last()
                    if current_stage:
                        current_stage.output_weight = output_weight
                        current_stage.powder_weight = powder_weight
                        current_stage.save()
                    
                    # Mark Order Completed
                    order.output_weight = output_weight
                    order.powder_weight = powder_weight
                    order.status = 'completed'
                    order.save()
                    
                    return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET: Context for the board
    workshops = Workshop.objects.all()
    drafts = ManufacturingOrder.objects.filter(status='draft').order_by('-id')
    
    # Active orders grouped by current workshop
    active_by_workshop = {}
    for ws in workshops:
        active_by_workshop[ws.id] = ManufacturingOrder.objects.filter(
            workshop=ws, 
            status__in=['in_progress', 'casting', 'crafting', 'polishing', 'qc_pending']
        ).prefetch_related('stages')

    context = {
        'workshops': workshops,
        'drafts': drafts,
        'active_by_workshop': active_by_workshop,
        'stones': Stone.objects.filter(current_stock__gt=0),
        'treasuries': Treasury.objects.all(),
    }
    return render(request, 'manufacturing/magic_workflow.html', context)
