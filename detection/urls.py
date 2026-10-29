from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Auth
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Patient Management
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/new/', views.patient_create_view, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail_view, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_edit_view, name='patient_edit'),
    path('patients/<int:pk>/history/', views.patient_history_view, name='patient_history'),

    # Screening & Testing
    path('test/new/', views.test_create_view, name='test_create'),
    path('test/<str:test_id>/result/', views.test_result_view, name='test_result'),
    path('test/<str:test_id>/report/', views.report_html_view, name='report_html'),
    path('test/<str:test_id>/report/pdf/', views.report_pdf_download_view, name='report_pdf'),

    # Overall History
    path('history/', views.all_history_view, name='all_history'),
]
