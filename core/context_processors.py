from core.models import GoldPrice, Carat
from manufacturing.models import ManufacturingOrder
from django.db.models import Sum, Count, Q

def gold_prices(request):
    # 1. Get latest price per carat in ONE query using Postgres distinct
    # This replaces the loop of queries
    prices = list(GoldPrice.objects.filter(carat__is_active=True)
                 .select_related('carat')
                 .order_by('carat', '-updated_at')
                 .distinct('carat'))
    
    # Sort by name for consistency (Python side sorting is fine)
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
        total_weight=Coalesce(Sum('input_weight'), 0)
    )
    
    # Add Coalesce if needed or just use stats
    # We need Coalesce for Sum
    from django.db.models.functions import Coalesce

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
