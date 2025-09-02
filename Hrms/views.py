from datetime import date
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
from datetime import date




# API_BASE_URL = "http://127.0.0.1:8002/hrms_backend/api/"
API_BASE_URL = "https://apnahrms.com/hrms_backend/api/"

# ... (other views) ...

def dashboard(request):
    """
    Displays the main dashboard, fetches all necessary user data,
    and correctly determines if the user is a manager.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "Your session has expired. Please log in.")
        return redirect('login')

    user_profile = request.session['user_profile']
    employee_id = user_profile.get('employee_id')
    
    context = {
        'first_name': user_profile.get('first_name', 'User'),
        'total_hours': "0.00",
        'is_manager': False
    }

    if not employee_id:
        messages.error(request, "Could not find your employee ID in the session.")
        return render(request, 'hrms/dashboard.html', context)

    try:
        # API Call 1: Get tasks to calculate total hours
        tasks_api_url = f"{API_BASE_URL}employee_task_list/{employee_id}/"
        tasks_response = requests.get(tasks_api_url, timeout=5)

        if tasks_response.ok:
            tasks_data = tasks_response.json().get('message_data', [])
            total_hours = sum(
                float(task.get('hours_spent', 0) or 0)
                for task in tasks_data
                if task.get('task_status') == 'Completed'
            )
            context['total_hours'] = f"{total_hours:.2f}"
        else:
            messages.warning(request, "Could not fetch task data.")

        # API Call 2: Check if the user is a manager
        team_api_url = f"{API_BASE_URL}get_my_team/"
        payload = {"manager_employee_id": employee_id}
        team_response = requests.post(team_api_url, json=payload, timeout=5)

        if team_response.ok:
            team_data = team_response.json()
            if team_data.get("message_code") == 1000 and team_data.get("message_data"):
                context['is_manager'] = True

    except requests.exceptions.RequestException:
        messages.error(request, "Could not connect to the backend server to load dashboard data.")

    return render(request, 'hrms/dashboard.html', context)



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





def login_view(request):
    # If user is already logged in, redirect them away from the login page
    if 'user_profile' in request.session:
        return redirect('dashboard')

    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        mobile_no = request.POST.get('mobile_no')
        pin = request.POST.get('pin')

        # api_url = "https://drishtis.app/hrms_backend/api/employee_login/"
        api_url = "https://apnahrms.com/hrms_backend/api/employee_login/"

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


def logout_view(request):
    request.session.clear()  # Clears all session data, keeps same session key
    return redirect('login')







# API_BASE_URL = "http://127.0.0.1:8002/hrms_backend/api/"
API_BASE_URL = "https://apnahrms.com/hrms_backend/api/"

def add_task(request):
    """
    A view for a logged-in user to add a task for THEMSELVES,
    with session management handled directly inside the view.
    """

    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to add a task.")
        return redirect('login')

    # If the code reaches this point, the user is definitely logged in.
    user_profile = request.session.get('user_profile')
    employee_id = user_profile.get('employee_id')

    if not employee_id:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect('login')

    context = {
        "projects": [],
        "task_types": [],
        "form_data": {},
        "user_profile": user_profile,
        "today": date.today(),
        "check_date_api_url": f"{API_BASE_URL}check_date_status/" 
    }

    try:
        # Fetch Projects
        proj_url = f"{API_BASE_URL}project_list_api/"
        proj_resp = requests.get(proj_url, timeout=5)
        if proj_resp.ok:
            proj_data = proj_resp.json()
            context["projects"] = proj_data.get("message_data", proj_data) if isinstance(proj_data, dict) else proj_data
        else:
            messages.error(request, f"Error loading Projects (Status: {proj_resp.status_code}).")

        # Fetch Task Types
        type_url = f"{API_BASE_URL}tasktype_list_api/"
        type_resp = requests.get(type_url, timeout=5)
        if type_resp.ok:
            type_data = type_resp.json()
            context["task_types"] = type_data.get("message_data", type_data) if isinstance(type_data, dict) else type_data
        else:
            messages.error(request, f"Error loading Task Types (Status: {type_resp.status_code}).")
        
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network Error: Could not connect to the backend server. {e}")
        return render(request, "hrms/add_task.html", context)

    if request.method == "POST":
        payload = {
            "employee": employee_id,
            "project": request.POST.get("project"),
            "date": request.POST.get("date"),
            "task_type": request.POST.get("task_type"),
            "start_time": request.POST.get("start_time"),
            "hours_spent": request.POST.get("hours_spent") or None
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}insert_task/", json=payload, timeout=10)
            resp_data = response.json()

            if response.ok and resp_data.get("message_code") == 1000:
                messages.success(request, f"Task Added Successfully!")
                return redirect("add_task") 
            else:
                messages.error(request, f"API Error: {resp_data.get('message_text', 'An unknown error occurred.')}")
        
        except requests.exceptions.RequestException:
            messages.error(request, "Network Error: Failed to connect to create the task.")

        context["form_data"] = request.POST
        return render(request, "hrms/add_task.html", context)

    return render(request, "hrms/add_task.html", context)



def task_list(request):
    """
    Displays a list of all tasks for the currently logged-in employee.
    """

    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to view your tasks.")
        return redirect('login')

    user_profile = request.session['user_profile']
    employee_id = user_profile.get('employee_id')

    if not employee_id:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect('login')

    context = {
        'tasks': [], # Start with an empty list
        'user_profile': user_profile
    }

    try:
        api_url = f"{API_BASE_URL}employee_task_list/{employee_id}/"
        
        response = requests.get(api_url, timeout=10)

        if response.ok:
            data = response.json()
            context['tasks'] = data.get('message_data', [])
        else:
            messages.error(request, f"Failed to load tasks. The server responded with status {response.status_code}.")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network Error: Could not connect to the backend to fetch tasks. {e}")

    return render(request, 'hrms/task_list.html', context)



def edit_task(request, task_id):
    """
    GET: Displays a form to edit an existing task.
    POST: Submits the updated task data to the backend API.
    """

    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to edit tasks.")
        return redirect('login')

    context = {
        "task": {},
        "projects": [],
        "task_types": [],
        "task_id": task_id
    }


    try:
        proj_resp = requests.get(f"{API_BASE_URL}project_list_api/", timeout=5)
        if proj_resp.ok:
            proj_data = proj_resp.json()
            context["projects"] = proj_data.get("message_data", proj_data) if isinstance(proj_data, dict) else proj_data
        
        type_resp = requests.get(f"{API_BASE_URL}tasktype_list_api/", timeout=5)
        if type_resp.ok:
            type_data = type_resp.json()
            context["task_types"] = type_data.get("message_data", type_data) if isinstance(type_data, dict) else type_data
            
    except requests.exceptions.RequestException:
        messages.error(request, "Network Error: Could not load data for the edit form.")
        return redirect('task_list')


    task_api_url = f"{API_BASE_URL}task_detail_update/{task_id}/"

    if request.method == 'POST':
        payload = {
            "project": request.POST.get("project"),
            "date": request.POST.get("date"),
            "task_type": request.POST.get("task_type"),
            "start_time": request.POST.get("start_time"),
            "hours_spent": request.POST.get("hours_spent") or None
        }
        
        try:
            response = requests.put(task_api_url, json=payload, timeout=10)
            if response.ok and response.json().get('message_code') == 1000:
                messages.success(request, "Task updated successfully!")
                return redirect('task_list')
            else:
                resp_data = response.json()
                messages.error(request, f"API Error: {resp_data.get('message_text', 'Failed to update task.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "Network Error: Failed to connect to update the task.")
        
        context['task'] = payload
        return render(request, 'hrms/edit_task.html', context)


    try:
        task_detail_url = f"{API_BASE_URL}task_detail_update/{task_id}/"
        response = requests.get(task_detail_url, timeout=10)
        if response.ok:
            context['task'] = response.json().get('message_data', {})
        else:
            messages.error(request, "Could not fetch task details to edit.")
            return redirect('task_list')
    except requests.exceptions.RequestException:
        messages.error(request, "Network Error: Failed to fetch task details.")
        return redirect('task_list')

    return render(request, 'hrms/edit_task.html', context)



def complete_task(request, task_id):
    """
    Handles the 'Complete Task' button click.
    Calls the backend API to mark a task as completed.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to perform this action.")
        return redirect('login')

    if request.method == 'POST':
        try:

            api_url = f"{API_BASE_URL}task_complete_api/{task_id}/"
            
            response = requests.put(api_url, timeout=10)
            
            resp_data = response.json()
            if response.ok and resp_data.get('message_code') == 1000:
                messages.success(request, "Task marked as complete!")
            else:
                messages.error(request, f"API Error: {resp_data.get('message_text', 'Could not complete task.')}")

        except requests.exceptions.RequestException as e:
            messages.error(request, f"Network Error: Could not connect to complete the task. {e}")
    return redirect('task_list')



# Hrms/views.py
# ... (keep all your other views and imports)

def my_team_view(request):
    """
    Displays a list of employees who report to the logged-in manager.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to view your team.")
        return redirect('login')

    manager_profile = request.session['user_profile']
    manager_employee_id = manager_profile.get('employee_id')
    
    context = {
        'team_members': []
    }

    try:
        # Call the backend API to get the team list
        api_url = f"{API_BASE_URL}get_my_team/"
        payload = {"manager_employee_id": manager_employee_id}
        response = requests.post(api_url, json=payload, timeout=10)

        if response.ok and response.json().get('message_code') == 1000:
            context['team_members'] = response.json().get('message_data', [])
        else:
            messages.error(request, f"Could not load team members. API Error: {response.json().get('message_text')}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network Error: Could not connect to fetch team data. {e}")

    return render(request, 'hrms/my_team.html', context)


# def team_member_tasks_view(request, employee_id):
#     """
#     Displays tasks for a specific team member for the manager to review.
#     """
#     if 'user_profile' not in request.session:
#         messages.error(request, "You must be logged in to view team tasks.")
#         return redirect('login')
    
#      # --- THIS IS THE NEW LOGIC ---
#     today = date.today()
#     # 1. Get dates from the URL. If they don't exist, use the 1st of the month and today as defaults.
#     from_date_str = request.GET.get('from_date', today.replace(day=1).strftime('%Y-%m-%d'))
#     to_date_str = request.GET.get('to_date', today.strftime('%Y-%m-%d'))

#     context = {
#         'tasks': [], 
#         'team_member': None,
#         'from_date': from_date_str, # 2. Pass these dates back to the template
#         'to_date': to_date_str
#     }
#     # --- END OF NEW LOGIC ---

#     context = {'tasks': [], 'team_member': None}

#     try:
#         # Get all tasks for the selected team member
#         api_url = f"{API_BASE_URL}employee_task_list/{employee_id}/"
#         response = requests.get(api_url, timeout=10)

#         if response.ok and response.json().get('message_code') == 1000:
#             tasks_data = response.json().get('message_data', [])
#             context['tasks'] = tasks_data
            
#             # For displaying the team member's name, find them in the API response
#             if tasks_data:
#                  # We need to fetch the employee name. The simplest way is another small API call or to pass it.
#                  # For simplicity, we assume we can construct it or it's part of the task data.
#                  # Let's assume the employee name can be fetched if needed, or we just show the ID.
#                  # To get the name, let's call the employee list once.
#                  emp_list_resp = requests.get(f"{API_BASE_URL}employee_list/", timeout=5)
#                  if emp_list_resp.ok:
#                      for emp in emp_list_resp.json():
#                          if emp['employee_id'] == employee_id:
#                              context['team_member'] = emp
#                              break
#         else:
#             messages.error(request, "Could not load tasks for this team member.")

#     except requests.exceptions.RequestException as e:
#         messages.error(request, f"Network Error: Could not fetch tasks. {e}")

#     return render(request, 'hrms/team_member_tasks.html', context)



# Hrms/views.py
from datetime import date
import requests
from django.shortcuts import render, redirect
from django.contrib import messages

# ... (other views like dashboard, add_task, etc.) ...

def team_member_tasks_view(request, employee_id):
    """
    Displays tasks for a specific team member. 
    Shows ALL tasks by default, or filters by date range if a search is performed.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to view team tasks.")
        return redirect('login')
    
    # 1. --- Prepare the Context and Default Dates for the FORM ---
    today = date.today()
    context = {
        'tasks': [], 
        'team_member': None,
        # These dates are ONLY for populating the hidden form fields
        'from_date': today.replace(day=1).strftime('%Y-%m-%d'),
        'to_date': today.strftime('%Y-%m-%d')
    }

    try:
        # 2. --- Fetch Employee Details (Always) ---
        emp_resp = requests.get(f"{API_BASE_URL}employee_update/{employee_id}/", timeout=5)
        if emp_resp.ok:
            context['team_member'] = emp_resp.json()
        else:
            messages.error(request, "Could not find the specified team member.")
            return redirect('my_team')

        # 3. --- Build the API URL Intelligently ---
        # Start with the base URL to get ALL tasks
        api_url = f"{API_BASE_URL}employee_task_list/{employee_id}/"

        # Check if the user has performed a date search
        from_date_str = request.GET.get('from_date')
        to_date_str = request.GET.get('to_date')

        # If they searched, add the date filters to the API call
        if from_date_str and to_date_str:
            api_url += f"?from_date={from_date_str}&to_date={to_date_str}"
            # Also, update the context to keep the searched dates in the form
            context['from_date'] = from_date_str
            context['to_date'] = to_date_str

        # 4. --- Fetch the Tasks ---
        response = requests.get(api_url, timeout=10)
        if response.ok and response.json().get('message_code') == 1000:
            context['tasks'] = response.json().get('message_data', [])
        
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network Error: Could not fetch data. {e}")

    # 5. --- Render the Page ---
    return render(request, 'hrms/team_member_tasks.html', context)




def approve_task_view(request):
    """
    Handles the 'Approve' button click from the manager's view.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "Session expired. Please log in.")
        return redirect('login')

    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        team_member_id = request.POST.get('employee_id')
        manager_user_id = request.session['user_profile'].get('user_id') # Assumes user_id is in session

        if not manager_user_id:
            messages.error(request, "Your user ID could not be found in your session.")
            return redirect('my_team')

        try:
            api_url = f"{API_BASE_URL}approve_employee_task/"
            payload = {"task_id": task_id, "approved_by_id": manager_user_id}
            response = requests.put(api_url, json=payload, timeout=10)
            
            resp_data = response.json()
            if response.ok and resp_data.get('message_code') == 1000:
                messages.success(request, "Task approved successfully!")
            else:
                messages.error(request, f"API Error: {resp_data.get('message_text')}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Network Error: {e}")

        return redirect('team_member_tasks', employee_id=team_member_id)

    return redirect('my_team')


def reject_task_view(request):
    """
    Handles the 'Reject' button click from the manager's view.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "Session expired. Please log in.")
        return redirect('login')

    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        team_member_id = request.POST.get('employee_id')
        rejection_reason = request.POST.get('rejection_reason', 'Rejected by manager.')
        manager_user_id = request.session['user_profile'].get('user_id')

        if not manager_user_id:
            messages.error(request, "Your user ID could not be found in your session.")
            return redirect('my_team')

        try:
            api_url = f"{API_BASE_URL}reject_employee_task/"
            payload = {
                "task_id": task_id,
                "rejected_by_id": manager_user_id,
                "rejected_reason": rejection_reason
            }
            response = requests.put(api_url, json=payload, timeout=10)

            resp_data = response.json()
            if response.ok and resp_data.get('message_code') == 1000:
                messages.success(request, "Task rejected successfully!")
            else:
                messages.error(request, f"API Error: {resp_data.get('message_text')}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Network Error: {e}")

        return redirect('team_member_tasks', employee_id=team_member_id)

    return redirect('my_team')    



def past_timesheet_view(request, employee_id):
    """
    Shows a date search form and displays ALL tasks for an employee
    within the selected date range.
    """
    if 'user_profile' not in request.session:
        return redirect('login')

    today = date.today()
    from_date_str = request.GET.get('from_date', today.replace(day=1).strftime('%Y-%m-%d'))
    to_date_str = request.GET.get('to_date', today.strftime('%Y-%m-%d'))

    context = {
        'tasks': [],
        'team_member': None,
        'from_date': from_date_str,
        'to_date': to_date_str
    }

    try:
        # Fetch employee details first
        emp_resp = requests.get(f"{API_BASE_URL}employee_update/{employee_id}/", timeout=5)
        if emp_resp.ok:
            context['team_member'] = emp_resp.json()
        else:
            messages.error(request, "Could not find the specified team member.")
            return redirect('my_team')

        # Call the API with the date range to get the tasks
        api_url = f"{API_BASE_URL}employee_task_list/{employee_id}/?from_date={from_date_str}&to_date={to_date_str}"
        response = requests.get(api_url, timeout=10)

        if response.ok and response.json().get('message_code') == 1000:
            context['tasks'] = response.json().get('message_data', [])

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network Error: Could not fetch data. {e}")

    return render(request, 'hrms/past_timesheet.html', context)



# your_APNA_HRMS_app/views.py
ADMIN_PANEL_URL = "http://127.0.0.1:8000" # Change port if needed

def employee_holiday_list_view(request):
    # 1. Check if the user is logged in by looking for their profile in the session.
    if 'user_profile' not in request.session:
        messages.error(request, "Please log in to view this page.")
        return redirect('login') # Redirect to your employee login page name

    user_profile = request.session['user_profile']
    employee_id = user_profile.get('employee_id')

    if not employee_id:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect('login')

    holidays = []
    company_info = {}
    
    try:
        # 2. Call the API to find out which company this employee belongs to.
        comp_api_url = f"{API_BASE_URL}get_employee_company/{employee_id}/"
        comp_response = requests.get(comp_api_url)
        
        if comp_response.status_code == 200:
            company_info = comp_response.json().get("message_data", {})
            company_id = company_info.get("company_id")

            # 3. If a company was found, make ONE API call to get its holidays.
            if company_id:
                holiday_api_url = f"{API_BASE_URL}get_holidays/"
                payload = {'company_id': company_id}
                holiday_response = requests.post(holiday_api_url, json=payload)
                if holiday_response.status_code == 200:
                    holidays = holiday_response.json().get("message_data", [])
                    for holiday in holidays:
                        date_str = holiday.get('actual_date')
                        if date_str:
                            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                            holiday['actual_date'] = date_obj.strftime('%d/%m/%y')
        else:
            # This is the error you were seeing. It means the employee has no company assigned.
            messages.error(request, "Could not determine your assigned company.")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Could not connect to the server: {e}")

    context = {
        'holidays': holidays,
        'company_info': company_info,
        'admin_panel_url': ADMIN_PANEL_URL,
        'first_name': user_profile.get('first_name', 'Employee')
    }
    return render(request, 'holidays/employee_holiday_list.html', context)



# your_APNA_HRMS_app/views.py

# Make sure these imports are at the top of the file
import os
import datetime
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
from xhtml2pdf import pisa
# ... and your other imports

def holiday_download_pdf_view(request):
    # This logic now lives inside your APNA HRMS project
    company_id = request.GET.get('company_id')
    company_name = request.GET.get('company_name', 'Report')

    if not company_id:
        # In a real app, you'd show an error, but for simplicity, we'll return an empty response
        return HttpResponse("Company ID is required.", status=400)

    api_url = f"{API_BASE_URL}get_holidays/"
    payload = {'company_id': company_id}
    response = requests.post(api_url, json=payload)
    holidays = response.json().get("message_data", [])

    for holiday in holidays:
        # The date from the API is a string like "2025-08-28"
        date_str = holiday.get('actual_date')
        if date_str:
            # Convert the string to a datetime object
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            # Format it back into the "dd/mm/yy" string and update the dictionary
            holiday['actual_date'] = date_obj.strftime('%d/%m/%y')

    context = {'holidays': holidays, 'company_name_for_title': company_name}
    html_string = render_to_string('holidays/pdf_template.html', context)
    
    result = BytesIO()
    pisa.CreatePDF(BytesIO(html_string.encode("UTF-8")), dest=result)
    pdf_file = result.getvalue()

    # NOTE: This will only save the file if your APNA HRMS project has MEDIA_ROOT set up.
    # If not, it will still download correctly.
    if hasattr(settings, 'MEDIA_ROOT'):
        safe_company_name = company_name.replace(' ', '_')
        pdf_save_dir = os.path.join(settings.MEDIA_ROOT, 'pdf', str(company_id), safe_company_name)
        os.makedirs(pdf_save_dir, exist_ok=True)
        filename = f"holiday_report_{safe_company_name}_{datetime.datetime.now().strftime('%d-%m-%y')}.pdf"
        pdf_save_path = os.path.join(pdf_save_dir, filename)
        with open(pdf_save_path, 'wb') as f:
            f.write(pdf_file)
    else:
        filename = "holiday_report.pdf"
        
    view_type = request.GET.get('view', 'attachment')
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'{view_type}; filename="{filename}"'
    
    return response

# incidence --------------




def add_incident_view(request):
    """
    GET: Renders the form to add a new incident.
    POST: Submits the new incident data to the backend API.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to report an incident.")
        return redirect('login')

    user_profile = request.session['user_profile']
    employee_id = user_profile.get('employee_id')
    user_id = user_profile.get('user_id') 

    if not employee_id or not user_id:
        messages.error(request, "Your session is invalid. Please log in again.")
        return redirect('login')

    if request.method == 'POST':
        payload = {
            'reported_by': employee_id,
            'created_by': user_id,
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'severity': request.POST.get('severity'),
            'incident_department': request.POST.get('incident_department')
        }
        
        photos = request.FILES.getlist('photos')
        files_to_send = [('photos', (photo.name, photo.read(), photo.content_type)) for photo in photos]

        try:
            api_url = f"{API_BASE_URL}incidents_add/"

             # --- DEBUGGING PRINTS ---
            # print("--- Sending Request to API ---")
            # print(f"URL: {api_url}")
            # print(f"Payload (Data): {payload}")
            # print(f"Files to send: {[f[0] for f in files_to_send]}") # Print just the keys to avoid large output
            # --- END DEBUGGING ---
            response = requests.post(api_url, data=payload, files=files_to_send, timeout=15)
            
            resp_data = response.json()
            if response.status_code == 201 and resp_data.get('message_code') == 1000:
                messages.success(request, "Incident reported successfully!")
                return redirect('incident_list')
            else:
                error_msg = resp_data.get('message_text', 'An unknown error occurred.')
                messages.error(request, f"API Error: {error_msg}")

        except requests.exceptions.RequestException as e:
            messages.error(request, f"Network Error: Could not connect to the server. {e}")
        
        context = {'form_data': request.POST}
        return render(request, 'incidence/add_incident.html', context)

    return render(request, 'incidence/add_incident.html')


def incident_list_view(request):
    """
    Displays a list of incidents reported by the logged-in employee.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in to view incidents.")
        return redirect('login')

    user_profile = request.session['user_profile']
    employee_id = user_profile.get('employee_id')

    context = {'incidents': []}
    if not employee_id:
        messages.error(request, "Your session is invalid.")
        return redirect('login')

    try:
        api_url = f"{API_BASE_URL}get_incidents_by_employee/" 
        payload = {'reported_by_id': employee_id}
        response = requests.post(api_url, json=payload, timeout=10)

        if response.ok:
            data = response.json()
            if data.get('message_code') == 1000:
                context['incidents'] = data.get('message_data', [])
        else:
            messages.error(request, f"Failed to load incidents. Server responded with status {response.status_code}.")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network Error: Could not connect to fetch incidents. {e}")

    return render(request, 'incidence/incident_list.html', context)


def view_incident_log_view(request, incident_id):
    """
    GET: Displays the conversation log for a specific incident.
    POST: Adds a new remark to the incident.
    """
    if 'user_profile' not in request.session:
        messages.error(request, "You must be logged in.")
        return redirect('login')

    user_profile = request.session['user_profile']
    user_id = user_profile.get('user_id')
    context = {'incident_id': incident_id}

    try:
        details_api_url = f"{API_BASE_URL}get_incident_details/{incident_id}/"
        details_response = requests.get(details_api_url, timeout=10)

        if not details_response.ok:
            messages.error(request, "Could not fetch incident details.")
            return redirect('incident_list')
        
        incident_data = details_response.json().get('message_data', {})
        if incident_data.get('remarks_log'):
            # Split the log and trim whitespace from each entry.
            incident_data['remarks_log_list'] = [
                entry.strip() for entry in incident_data['remarks_log'].split('---') if entry.strip()
            ]
        context['incident'] = incident_data

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Network Error: {e}")
        return redirect('incident_list')

    if request.method == 'POST':
        payload = {
            "incident_id": incident_id,
            "user_id": user_id,
            "remark_text": request.POST.get("remark_text"),
        }
        try:
            update_api_url = f"{API_BASE_URL}remark_incidents/"
            response = requests.put(update_api_url, json=payload, timeout=10)
            resp_data = response.json()

            if response.ok and resp_data.get('message_code') == 1000:
                messages.success(request, "Your remark has been added.")
            else:
                messages.error(request, f"API Error: {resp_data.get('message_text', 'Failed to add remark.')}")
        except requests.exceptions.RequestException:
            messages.error(request, "Network Error: Could not submit your remark.")
        
        return redirect('view_incident_log', incident_id=incident_id)

    return render(request, 'incidence/view_incident_log.html', context)