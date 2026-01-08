from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Category

@require_GET
def get_next_barcode(request):
    """API endpoint to get next barcode for a category"""
    category_id = request.GET.get('category_id')
    
    if not category_id:
        return JsonResponse({'error': 'Category ID required'}, status=400)
    
    try:
        category = Category.objects.get(id=category_id)
        barcode = category.get_next_barcode()
        
        if barcode:
            return JsonResponse({'barcode': barcode})
        else:
            return JsonResponse({'error': 'Category has no barcode prefix'}, status=400)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
