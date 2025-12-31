from django.shortcuts import render
from django.db.models import Sum, Count
from .models import Item, Category, RawMaterial
from core.models import Carat, Branch

def inventory_dashboard(request):
    # Total stats
    total_items = Item.objects.filter(status='available').count()
    total_gold_weight = Item.objects.filter(status='available').aggregate(Sum('net_gold_weight'))['net_gold_weight__sum'] or 0
    total_raw_weight = RawMaterial.objects.aggregate(Sum('current_weight'))['current_weight__sum'] or 0
    
    # Items by status
    status_counts = Item.objects.values('status').annotate(count=Count('id'))
    
    # Items by carat
    carat_stats = Item.objects.values('carat__name').annotate(
        count=Count('id'),
        weight=Sum('net_gold_weight')
    )
    
    # Recent items
    recent_items = Item.objects.order_by('-created_at')[:10]
    
    # Branch distribution
    branch_stats = Item.objects.values('current_branch__name').annotate(
        count=Count('id'),
        weight=Sum('net_gold_weight')
    )

    context = {
        'total_items': total_items,
        'total_gold_weight': total_gold_weight,
        'total_raw_weight': total_raw_weight,
        'status_counts': status_counts,
        'carat_stats': carat_stats,
        'recent_items': recent_items,
        'branch_stats': branch_stats,
    }
    return render(request, 'inventory/dashboard.html', context)

from django.shortcuts import get_object_or_404
def print_tags(request):
    """طباعة باركود القطع (Jewelry Tags)"""
    ids = request.GET.get('ids', '').split(',')
    items = Item.objects.filter(id__in=[id for id in ids if id])
    
    if not items.exists():
        # If no specific IDs, maybe show recent or all available? 
        # But usually this is called from admin action.
        pass
        
    return render(request, 'inventory/print_tags.html', {'items': items})

