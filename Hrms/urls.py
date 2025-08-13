from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('upload-cash-photo/', views.upload_cash_photo, name='upload_cash_photo'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


]