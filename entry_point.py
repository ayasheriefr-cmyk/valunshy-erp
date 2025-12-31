import os
import sys
import webbrowser
from threading import Timer
from waitress import serve
from backend.wsgi import application

def open_browser():
    webbrowser.open_new('http://127.0.0.1:8000/')

if __name__ == '__main__':
    # Set Django Settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    
    # Run Migrations (Optional but good for portability)
    # import django
    # django.setup()
    # from django.core.management import call_command
    # call_command('migrate')
    
    print("Starting Valunshy Jewelry ERP...")
    print("Please wait while the system loads...")
    
    # Open Browser after 1.5 seconds
    Timer(1.5, open_browser).start()
    
    # Start Waitress Server
    serve(application, host='127.0.0.1', port=8000)
