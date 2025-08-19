from django.http import HttpResponse
import requests
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import uuid

def login_view(request):
    # If user is already logged in, redirect them away from the login page
    if 'user_profile' in request.session:
        return redirect('dashboard')

    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        mobile_no = request.POST.get('mobile_no')
        pin = request.POST.get('pin')

        api_url = "https://drishtis.app/hrms_backend/api/employee_login/"
        payload = {
            "company_id": company_id,
            "mobile_no": mobile_no,
            "pin": pin
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("message_code") == 1000:
                user_profile = data["message_data"][0]

                # Store full profile in session
                request.session['user_profile'] = user_profile
                request.session['is_logged_in'] = True

                return redirect('dashboard')
            else:
                error_message = data.get("message_text", "Invalid credentials or user not found.")
                messages.error(request, error_message)

        except requests.exceptions.RequestException:
            messages.error(request, "Could not connect to the login service. Please try again later.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")

    return render(request, 'hrms/login.html')


# Create your views here.
def dashboard(request):
    user_profile = request.session.get('user_profile', {})
    first_name = user_profile.get('first_name', 'Guest')  # Default to "Guest" if missing
    return render(request, 'hrms/dashboard.html', {'first_name': first_name})


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

def logout_view(request):
    request.session.clear()  # Clears all session data, keeps same session key
    return redirect('login')
