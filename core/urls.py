from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('subjects/', views.subjects_list, name='subjects'),
    path('subjects/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    
    path('pyqs/', views.pyqs_list, name='pyqs'),
    path('pyqs/download/<int:pyq_id>/', views.download_pyq, name='download_pyq'),
    
    path('tests/', views.tests_list, name='tests'),
    path('tests/<int:test_id>/', views.test_detail, name='test_detail'),
    path('tests/<int:test_id>/take/', views.take_test, name='take_test'),
    path('tests/<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('attempts/<int:attempt_id>/result/', views.test_result, name='test_result'),
    
    path('subscriptions/', views.subscriptions_view, name='subscriptions'),
    path('payments/initiate/<int:plan_id>/', views.initiate_payment, name='initiate_payment'),
    path('payments/verify/', views.verify_payment, name='verify_payment'),
    
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),
]
