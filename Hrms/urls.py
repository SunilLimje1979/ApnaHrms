from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('upload-cash-photo/', views.upload_cash_photo, name='upload_cash_photo'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('TaskAdd/', views.TaskAdd, name='TaskAdd'),
    path('task_list/', views.task_list_view, name='task_list'),
    path('task_complete/<int:task_id>/', views.task_complete_view, name='task_complete'),

    path('team/approvals/', views.team_approvals_view, name='team_approvals'),
    path('team/task/approve/<int:task_id>/', views.task_approve_view, name='task_approve'),
    path('team/task/reject/<int:task_id>/', views.task_reject_view, name='task_reject'),

    path('timesheet/', views.timesheet_page_view, name='timesheet_page'),

   



]