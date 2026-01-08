from core.models import GoldPrice, Carat
from manufacturing.models import ManufacturingOrder
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce as DbCoalesce
from decimal import Decimal

def gold_prices(request):
    # 1. Get latest price per carat (SQLite Compatible)
    # Fetch all prices ordered by updated_at desc
    all_prices = GoldPrice.objects.filter(carat__is_active=True).select_related('carat').order_by('-updated_at')
    
    # Deduplicate in Python (keep first occurrence per carat)
    seen_carats = set()
    prices = []
    for p in all_prices:
        if p.carat_id not in seen_carats:
            prices.append(p)
            seen_carats.add(p.carat_id)
    
    # Sort by name for consistency
    prices.sort(key=lambda x: x.carat.name)
    
    # 2. Consolidated Manufacturing Stats in ONE aggregation
    # Exclude completed and cancelled
    mfg_stats_aggr = ManufacturingOrder.objects.exclude(
        status__in=['completed', 'cancelled', 'draft']
    ).aggregate(
        total_count=Count('id'),
        casting_count=Count('id', filter=Q(status='casting')),
        crafting_count=Count('id', filter=Q(status='crafting')),
        polishing_count=Count('id', filter=Q(status='polishing')),
        total_weight=DbCoalesce(Sum('input_weight'), Decimal('0'))
    )
    
    mfg_stats = {
        'count': mfg_stats_aggr['total_count'],
        'casting': mfg_stats_aggr['casting_count'],
        'crafting': mfg_stats_aggr['crafting_count'],
        'polishing': mfg_stats_aggr['polishing_count'],
        'weight': mfg_stats_aggr['total_weight'],
    }
    
    return {
        'live_gold_prices': prices,
        'global_mfg_stats': mfg_stats
    }
