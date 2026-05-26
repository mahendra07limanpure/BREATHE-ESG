from django.urls import path
from ingestion import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('records/review/', views.review_records, name='review_records'),
    path('records/<int:record_id>/approve/', views.approve_record, name='approve_record'),
    path('records/<int:record_id>/reject/', views.reject_record, name='reject_record'),
    path('records/<int:record_id>/audit/', views.audit_trail, name='audit_trail'),
    path('summary/co2/', views.co2_summary, name='co2_summary'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
