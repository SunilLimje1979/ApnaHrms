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



# your_app/views.py

import requests
from django.shortcuts import render, redirect
from django.contrib import messages

def TaskAdd(request):
    """Shows the task form (GET) and calls the Task Insert API (POST)."""
    url = "https://drishtis.app/hrms_backend/api/"

    # --- Helper function to get dropdown data. This avoids repeating code. ---
    def get_dropdown_data():
        context = {"employees": [], "projects": [], "task_types": []}
        try:
            emp_resp = requests.get(f"{url}employee_list_api/", verify=False)
            proj_resp = requests.get(f"{url}project_list_api/", verify=False)
            type_resp = requests.get(f"{url}task_type_list_api/", verify=False)

            if emp_resp.ok: context["employees"] = emp_resp.json()
            if proj_resp.ok: context["projects"] = proj_resp.json()
            if type_resp.ok: context["task_types"] = type_resp.json()
        except requests.exceptions.RequestException:
            messages.error(request, "Could not load dropdown data from the server.")
        return context

    # --- Handle the form submission ---
    if request.method == "POST":
        payload = {
            "employee": request.POST.get("employee"),
            "project": request.POST.get("project"),
            "date": request.POST.get("date"),
            "task_type": request.POST.get("task_type"),
            "start_time": request.POST.get("start_time"),
        }
        # Add optional fields to the payload ONLY if they have a value
        optional_fields = [
            "end_time", "hours_spent", "billable_YN", "task_status", 
            "submission_date", "submitted_on", "approved_by_id", 
            "approved_on", "rejected_reason", "end_date"
        ]
        for field in optional_fields:
            if request.POST.get(field):
                payload[field] = request.POST.get(field)

        try:
            response = requests.post(f"{url}insert_task/", json=payload, verify=False)
            response.raise_for_status()  # This will raise an error for 4xx/5xx status codes
            resp_data = response.json()

            if resp_data.get("message_code") == 1000:
                messages.success(request, "Task Added Successfully!")
                return redirect("task_list")  # Make sure you have a URL named 'task_list'
            else:
                messages.error(request, f"API Error: {resp_data.get('message_text', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            error_message = "Failed to connect to the Task API."
            # Try to get a more specific error from the API response if it exists
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message_text', 'An API error occurred.')
                except ValueError: # If response is not JSON
                    pass
            messages.error(request, error_message)

        # --- If submission fails, re-render the form with the user's data ---
        context = get_dropdown_data()  # We need the dropdowns again
        context["form_data"] = request.POST  # Pass the submitted data back to the template
        return render(request, "hrms/tasks_insert.html", context)

    # --- Handle the initial page load (GET request) ---
    context = get_dropdown_data()
    return render(request, "hrms/tasks_insert.html", context)




def task_list_view(request):
    """Fetches and displays a list of tasks for the logged-in employee."""
    # if 'user_profile' not in request.session:
    #     return redirect('login')

    user_profile = request.session.get('user_profile', {})
    employee_id = user_profile.get('employee_id')
    company_id = user_profile.get('Company_Id')

    # if not employee_id or not company_id:
    #     messages.error(request, "Session invalid. Please log in again.")
    #     return redirect('login')

    filter_date_str = request.GET.get('date', date.today().strftime("%Y-%m-%d"))
    api_url = "https://drishtis.app/hrms_backend/api/get_timesheets_by_date/"
    payload = {"employee_id": employee_id, "company_id": company_id, "date": filter_date_str}
    
    tasks = []
    try:
        response = requests.post(api_url, json=payload, verify=False, timeout=10)
        response.raise_for_status()
        resp_data = response.json()
        if resp_data.get("message_code") == 1000:
            tasks = resp_data.get("message_data", [])
    except requests.exceptions.RequestException:
        messages.error(request, "Could not fetch tasks from the server.")

    context = {'tasks': tasks, 'filter_date': filter_date_str}
    return render(request, 'hrms/task_list.html', context)


def task_complete_view(request, task_id):
    """Handles the request to complete a task by calling the external API."""
    if request.method != 'POST':
        messages.error(request, "Invalid action.")
        return redirect('task_list')

    api_url = f"https://drishtis.app/hrms_backend/api/task_complete_api/{task_id}/"
    try:
        response = requests.put(api_url, verify=False, timeout=10)
        response.raise_for_status()
        resp_data = response.json()
        if resp_data.get("message_code") == 1000:
            messages.success(request, "Task successfully marked as complete!")
        else:
            messages.error(request, f"Could not complete task: {resp_data.get('message_text', 'API error')}")
    except requests.exceptions.RequestException:
        messages.error(request, "Failed to connect to the server to complete the task.")

    # Redirect back to the task list to see the updated status
    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return redirect(referer_url) # Go back to the exact page the user was on
    return redirect('task_list')




def team_approvals_view(request):
    """
    Shows a list of all 'Completed' tasks from the manager's team members
    that are awaiting approval.
    """
    # if 'user_profile' not in request.session:
    #     return redirect('login')

    user_profile = request.session.get('user_profile', {})
    manager_employee_id = user_profile.get('employee_id')
    api_base_url = "https://drishtis.app/hrms_backend/api/"
    
    team_tasks_for_approval = []
    
    # 1. First, get the list of team members
    try:
        team_response = requests.post(f"{api_base_url}get_my_team/", json={"manager_employee_id": manager_employee_id}, verify=False)
        if team_response.ok:
            team_members = team_response.json().get("message_data", [])
            
            # 2. For each team member, get their timesheet for today (or a filtered date)
            for member in team_members:
                member_id = member.get('employee_id')
                from datetime import date
                today_str = date.today().strftime('%Y-%m-%d')
                
                payload = {
                    "manager_employee_id": manager_employee_id,
                    "team_member_employee_id": member_id,
                    "date": today_str  # For now, we fetch today's tasks. A filter could be added.
                }
                timesheet_response = requests.post(f"{api_base_url}get_team_member_timesheet_by_date_and_id/", json=payload, verify=False)
                
                if timesheet_response.ok:
                    tasks_data = timesheet_response.json().get("message_data", {})
                    tasks = tasks_data.get("tasks", [])
                    
                    # 3. Filter for only 'Completed' tasks and add employee info
                    for task in tasks:
                        if task.get('task_status') == 'Completed':
                            task['employee_name'] = member.get('full_name') # Add name for display
                            team_tasks_for_approval.append(task)

    except requests.RequestException:
        messages.error(request, "Could not connect to the server to fetch team tasks.")

    context = {
        'tasks_for_approval': team_tasks_for_approval
    }
    return render(request, 'hrms/team_approvals.html', context)




def task_approve_view(request, task_id):
    """Handles the manager's action to approve a task."""
    if request.method != 'POST':
        return redirect('team_approvals')

    user_profile = request.session.get('user_profile', {})
    # Your API for approval needs the Django User ID, which you store as 'user_Id' in the session
    approver_user_id = user_profile.get('user_Id') 

    if not approver_user_id:
        messages.error(request, "Your user ID is missing from the session. Cannot approve.")
        return redirect('team_approvals')

    api_url = "https://drishtis.app/hrms_backend/api/approve_employee_task/"
    payload = {"task_id": task_id, "approved_by_id": approver_user_id}
    
    try:
        response = requests.put(api_url, json=payload, verify=False)
        if response.ok and response.json().get("message_code") == 1000:
            messages.success(request, "Task approved successfully.")
        else:
            messages.error(request, f"Failed to approve task: {response.json().get('message_text')}")
    except requests.RequestException:
        messages.error(request, "Connection error while approving task.")
        
    return redirect('team_approvals')


def task_reject_view(request, task_id):
    """Handles the manager's action to reject a task."""
    if request.method != 'POST':
        return redirect('team_approvals')

    user_profile = request.session.get('user_profile', {})
    # Your API for rejection needs the Django User ID
    rejector_user_id = user_profile.get('user_Id')
    reason = request.POST.get('rejection_reason', 'No reason provided.')

    if not rejector_user_id:
        messages.error(request, "Your user ID is missing from the session. Cannot reject.")
        return redirect('team_approvals')

    api_url = "https://drishtis.app/hrms_backend/api/reject_employee_task/"
    payload = {"task_id": task_id, "rejected_by_id": rejector_user_id, "rejected_reason": reason}

    try:
        response = requests.put(api_url, json=payload, verify=False)
        if response.ok and response.json().get("message_code") == 1000:
            messages.success(request, "Task rejected successfully.")
        else:
            messages.error(request, f"Failed to reject task: {response.json().get('message_text')}")
    except requests.RequestException:
        messages.error(request, "Connection error while rejecting task.")

    return redirect('team_approvals')




# hrms/views.py
# Replace the existing team_approvals_view with this updated version

def team_approvals_view(request):
    """
    Shows a list of tasks from the manager's team members,
    with filters for date and status.
    """
    # if 'user_profile' not in request.session:
    #     return redirect('login')

    user_profile = request.session.get('user_profile', {})
    manager_employee_id = user_profile.get('employee_id')
    api_base_url = "https://drishtis.app/hrms_backend/api/"
    
    # --- 1. Get Filter Values from the URL ---
    # The URL will look like: /team/approvals/?from_date=...&to_date=...&status=...
    from datetime import date, timedelta
    
    # Default to today if no dates are provided
    today = date.today()
    from_date_str = request.GET.get('from_date', today.strftime('%Y-%m-%d'))
    to_date_str = request.GET.get('to_date', today.strftime('%Y-%m-%d'))
    status_filter = request.GET.get('status', 'Completed') # Default to show 'Completed' tasks

    # Convert string dates to date objects to loop through them
    from_date_obj = date.fromisoformat(from_date_str)
    to_date_obj = date.fromisoformat(to_date_str)
    
    all_team_tasks = []
    
    # --- 2. Call APIs using the filters ---
    try:
        # Get the list of team members once
        team_response = requests.post(f"{api_base_url}get_my_team/", json={"manager_employee_id": manager_employee_id}, verify=False)
        if not team_response.ok:
            messages.error(request, "Could not fetch your team list.")
            raise requests.RequestException # Stop processing

        team_members = team_response.json().get("message_data", [])
        
        # Loop through each day in the selected date range
        current_date = from_date_obj
        while current_date <= to_date_obj:
            date_to_fetch = current_date.strftime('%Y-%m-%d')
            
            # For each day, get tasks for every team member
            for member in team_members:
                payload = {
                    "manager_employee_id": manager_employee_id,
                    "team_member_employee_id": member.get('employee_id'),
                    "date": date_to_fetch
                }
                timesheet_response = requests.post(f"{api_base_url}get_team_member_timesheet_by_date_and_id/", json=payload, verify=False)
                
                if timesheet_response.ok:
                    tasks_data = timesheet_response.json().get("message_data", {})
                    tasks = tasks_data.get("tasks", [])
                    
                    for task in tasks:
                        task['employee_name'] = member.get('full_name') # Add employee name for display
                        all_team_tasks.append(task)
            
            current_date += timedelta(days=1) # Move to the next day

    except requests.RequestException:
        messages.error(request, "There was an error connecting to the timesheet server.")

    # --- 3. Filter the results by status ---
    filtered_tasks = []
    if status_filter != 'all':
        for task in all_team_tasks:
            # Handle both 'Started' (incomplete) and other statuses
            if status_filter == 'Incomplete':
                if task.get('task_status') == 'Started':
                    filtered_tasks.append(task)
            elif task.get('task_status') == status_filter:
                filtered_tasks.append(task)
    else:
        filtered_tasks = all_team_tasks

    # --- 4. Send all data to the template ---
    context = {
        'tasks_for_approval': filtered_tasks,
        'filters': {
            'from_date': from_date_str,
            'to_date': to_date_str,
            'status': status_filter
        }
    }
    return render(request, 'hrms/team_approvals.html', context)




def timesheet_page_view(request):
    """
    A comprehensive view that handles both the employee's own timesheet 
    and their team's timesheets if they are a manager.
    """
    # if 'user_profile' not in request.session:
    #     return redirect('login')

    user_profile = request.session.get('user_profile', {})
    employee_id = user_profile.get('employee_id')
    company_id = user_profile.get('Company_Id')
    api_base_url = "https://drishtis.app/hrms_backend/api/"
    
    # --- Determine the active tab from the URL (e.g., ?view=my_team) ---
    active_view = request.GET.get('view', 'my_timesheet')

    # --- Prepare data for the template ---
    context = {
        'user_profile': user_profile,
        'active_view': active_view,
        'my_tasks': [],
        'team_members': [],
        'selected_team_member_tasks': None,
        'selected_team_member_id': None,
        'filters': {}
    }

    # --- 1. Fetch data for the logged-in user's own timesheet ("My Timesheet" tab) ---
    from datetime import date
    my_timesheet_date = request.GET.get('my_date', date.today().strftime('%Y-%m-%d'))
    context['filters']['my_date'] = my_timesheet_date
    
    my_payload = {"employee_id": employee_id, "company_id": company_id, "date": my_timesheet_date}
    try:
        response = requests.post(f"{api_base_url}get_timesheets_by_date/", json=my_payload, verify=False)
        if response.ok:
            context['my_tasks'] = response.json().get("message_data", [])
    except requests.RequestException:
        messages.error(request, "Could not fetch your personal tasks.")

    # --- 2. Fetch data for the manager's team ("My Team" tab) ---
    # First, get the list of team members to see if the "My Team" tab should even be shown.
    try:
        team_response = requests.post(f"{api_base_url}get_my_team/", json={"manager_employee_id": employee_id}, verify=False)
        if team_response.ok:
            context['team_members'] = team_response.json().get("message_data", [])
    except requests.RequestException:
        # Don't show an error, just means the team list won't load
        pass

    # If the user is actively viewing the "My Team" tab and has selected a member...
    if active_view == 'my_team':
        selected_member_id = request.GET.get('team_member_id')
        if selected_member_id:
            context['selected_team_member_id'] = int(selected_member_id)
            team_filter_date = request.GET.get('team_date', date.today().strftime('%Y-%m-%d'))
            context['filters']['team_date'] = team_filter_date
            
            team_payload = {
                "manager_employee_id": employee_id,
                "team_member_employee_id": selected_member_id,
                "date": team_filter_date
            }
            try:
                response = requests.post(f"{api_base_url}get_team_member_timesheet_by_date_and_id/", json=team_payload, verify=False)
                if response.ok:
                    context['selected_team_member_tasks'] = response.json().get("message_data", {})
                else:
                    messages.error(request, f"Could not fetch timesheet for team member.")
            except requests.RequestException:
                messages.error(request, "Could not fetch team member's timesheet.")

    return render(request, 'hrms/timesheet_page.html', context)