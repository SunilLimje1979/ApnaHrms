from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('upload-cash-photo/', views.upload_cash_photo, name='upload_cash_photo'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('task_add/', views.add_task, name='add_task'),
    path('task_list/', views.task_list, name='task_list'),
    path('task_edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('task_complete/<int:task_id>/', views.complete_task, name='complete_task'),

    path('my_team/', views.my_team_view, name='my_team'),
    path('my_team_tasks/<int:employee_id>/', views.team_member_tasks_view, name='team_member_tasks'),
    path('my_team/task/approve/', views.approve_task_view, name='approve_task'),
    path('my_team/task/reject/', views.reject_task_view, name='reject_task'),

    path('my_team_past_timesheet/<int:employee_id>/', views.past_timesheet_view, name='past_timesheet_view'),

    path('employee_holiday_list/', views.employee_holiday_list_view, name='employee_holiday_list'),
    path('holidays/pdf/', views.holiday_download_pdf_view, name='apna_hrms_holiday_pdf'),

    path('add_incident/', views.add_incident_view, name='add_incident'),
    path('incident_list/', views.incident_list_view, name='incident_list'),
    path('view_incident_log_/<int:incident_id>/', views.view_incident_log_view, name='view_incident_log'),




]