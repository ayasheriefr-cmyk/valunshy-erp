from core.models import GoldPrice, Carat
from manufacturing.models import ManufacturingOrder
from django.db.models import Sum

def gold_prices(request):
    # Get latest price per carat
    prices = []
    for carat in Carat.objects.filter(is_active=True):
        latest_price = GoldPrice.objects.filter(carat=carat).order_by('-updated_at').first()
        if latest_price:
            prices.append(latest_price)
    
    # Sort by name for consistency
    prices.sort(key=lambda x: x.carat.name)
    
    # Manufacturing Stats for Global Dashboard access
    # Exclude completed and cancelled
    mfg_qs = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled', 'draft'])
    mfg_stats = {
        'count': mfg_qs.count(),
        'casting': mfg_qs.filter(status='casting').count(),
        'crafting': mfg_qs.filter(status='crafting').count(),
        'polishing': mfg_qs.filter(status='polishing').count(),
        'weight': mfg_qs.aggregate(t=Sum('input_weight'))['t'] or 0,
    }
    
    return {
        'live_gold_prices': prices,
        'global_mfg_stats': mfg_stats
    }
