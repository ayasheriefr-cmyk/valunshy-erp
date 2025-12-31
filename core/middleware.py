from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings

class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG and not request.user.is_authenticated:
            user = User.objects.filter(is_superuser=True).first()
            if user:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        response = self.get_response(request)
        return response
