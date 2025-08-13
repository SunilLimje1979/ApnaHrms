from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('upload-cash-photo/', views.upload_cash_photo, name='upload_cash_photo'),
]