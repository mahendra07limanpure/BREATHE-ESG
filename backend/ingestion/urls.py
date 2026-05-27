from django.urls import path
from ingestion import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('records/review/', views.review_records, name='review_records'),
    path('records/debug/', views.debug_records, name='debug_records'),
    path('records/clear/', views.clear_all_data, name='clear_all_data'),
    path('records/approve-all/', views.approve_all_records, name='approve_all_records'),
    path('records/reject-all/', views.reject_all_records, name='reject_all_records'),
    path('records/<int:record_id>/approve/', views.approve_record, name='approve_record'),
    path('records/<int:record_id>/reject/', views.reject_record, name='reject_record'),
    path('records/<int:record_id>/audit/', views.audit_trail, name='audit_trail'),
    path('summary/co2/', views.co2_summary, name='co2_summary'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('audit/report/', views.audit_report, name='audit_report'),
]
