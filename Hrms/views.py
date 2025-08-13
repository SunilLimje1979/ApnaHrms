from django.http import HttpResponse
import requests
from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.contrib import messages
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import uuid


# Create your views here.
def dashboard(request):
    return render(request, 'hrms/dashboard.html')

# views.py
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def upload_cash_photo(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded.'})

        # Save to MEDIA folder
        img_directory = os.path.join(settings.MEDIA_ROOT, 'cash_photos')
        os.makedirs(img_directory, exist_ok=True)

        file_path = os.path.join(img_directory, uploaded_file.name)

        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        file_url = f"{settings.MEDIA_URL}cash_photos/{uploaded_file.name}"

        return JsonResponse({'status': 'success', 'file_url': file_url})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})
