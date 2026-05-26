from django.contrib import admin

from .models import AuditLog, EmissionRecord, PlantMaster, UploadBatch


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "source_type", "file_name", "uploaded_by", "uploaded_at", "total_rows", "flagged_rows")
    search_fields = ("file_name", "uploaded_by")
    list_filter = ("source_type", "uploaded_at")


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "source_type", "scope", "activity_type", "record_date", "quantity_normalised", "unit_normalised", "co2_kg", "status", "is_locked")
    search_fields = ("activity_type", "site_name", "unit_normalised")
    list_filter = ("source_type", "scope", "status", "record_date", "is_locked")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "record_id", "action", "performed_by", "timestamp", "note")
    search_fields = ("performed_by", "note", "action")
    list_filter = ("action", "performed_by", "timestamp")


@admin.register(PlantMaster)
class PlantMasterAdmin(admin.ModelAdmin):
    list_display = ("id", "werks", "site_name", "city", "state")
    search_fields = ("werks", "site_name", "city", "state")
