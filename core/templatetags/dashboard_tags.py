from django import template
from manufacturing.models import ManufacturingOrder
from django.db.models import Sum

register = template.Library()

@register.simple_tag
def get_manufacturing_stats():
    # Helper to get manufacturing stats for dashboard
    qs = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled'])
    stats = {
        'count': qs.count(),
        'casting': qs.filter(status='casting').count(),
        'crafting': qs.filter(status='crafting').count(),
        'polishing': qs.filter(status='polishing').count(),
        'weight': qs.aggregate(t=Sum('input_weight'))['t'] or 0,
    }
    return stats

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
