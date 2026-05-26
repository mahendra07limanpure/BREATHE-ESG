import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum

from ingestion.models import EmissionRecord, UploadBatch, AuditLog
from ingestion.services.ingestion_service import ingest_file

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """Upload CSV file for ingestion."""
    if 'file' not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)

    if 'source_type' not in request.POST:
        return JsonResponse({"error": "source_type required"}, status=400)

    file_obj = request.FILES['file']
    source_type = request.POST.get('source_type')
    uploaded_by = request.POST.get('uploaded_by', 'analyst')

    # Save file temporarily
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        for chunk in file_obj.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        result = ingest_file(tmp_path, source_type, uploaded_by)
        return JsonResponse(result, status=200)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JsonResponse({"error": "Server error"}, status=500)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@require_http_methods(["GET"])
def review_records(request):
    """Get records pending review (status='flagged' or 'pending')."""
    source_type = request.GET.get('source_type')
    status = request.GET.get('status', 'pending')
    limit = int(request.GET.get('limit', 50))

    query = EmissionRecord.objects.all()

    if source_type:
        query = query.filter(source_type=source_type)

    if status:
        query = query.filter(status=status)

    records = query.order_by('created_at')[:limit]

    data = []
    for r in records:
        data.append({
            "id": r.id,
            "source_type": r.source_type,
            "scope": r.scope,
            "activity_type": r.activity_type,
            "site_name": r.site_name,
            "record_date": r.record_date.isoformat(),
            "quantity_raw": r.quantity_raw,
            "unit_raw": r.unit_raw,
            "quantity_normalised": r.quantity_normalised,
            "unit_normalised": r.unit_normalised,
            "co2_kg": r.co2_kg,
            "status": r.status,
            "flag_reason": r.flag_reason,
            "is_locked": r.is_locked,
        })

    return JsonResponse({"records": data, "count": len(data)}, status=200)


@csrf_exempt
@require_http_methods(["PATCH"])
def approve_record(request, record_id):
    """Approve a single record."""
    try:
        record = EmissionRecord.objects.get(id=record_id)
    except EmissionRecord.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    try:
        data = json.loads(request.body)
        note = data.get('note', '')
        performed_by = data.get('performed_by', 'analyst')
    except:
        note = ''
        performed_by = 'analyst'

    record.approve(performed_by=performed_by, note=note)

    return JsonResponse({
        "id": record.id,
        "status": record.status,
        "is_locked": record.is_locked,
        "message": "Record approved and locked"
    }, status=200)


@csrf_exempt
@require_http_methods(["PATCH"])
def reject_record(request, record_id):
    """Reject a single record."""
    try:
        record = EmissionRecord.objects.get(id=record_id)
    except EmissionRecord.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    try:
        data = json.loads(request.body)
        note = data.get('note', '')
        performed_by = data.get('performed_by', 'analyst')
    except:
        note = ''
        performed_by = 'analyst'

    record.reject(performed_by=performed_by, note=note)

    return JsonResponse({
        "id": record.id,
        "status": record.status,
        "message": "Record rejected"
    }, status=200)


@require_http_methods(["GET"])
def co2_summary(request):
    """Get CO2 totals by scope (approved records only)."""
    approved = EmissionRecord.objects.filter(status="approved")

    total_kg = approved.aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0
    scope_1_kg = approved.filter(scope="scope_1").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0
    scope_2_kg = approved.filter(scope="scope_2").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0
    scope_3_kg = approved.filter(scope="scope_3").aggregate(Sum("co2_kg"))["co2_kg__sum"] or 0

    return JsonResponse({
        "total_kg": round(total_kg, 2),
        "total_tonnes": round(total_kg / 1000, 2),
        "scope_1_kg": round(scope_1_kg, 2),
        "scope_2_kg": round(scope_2_kg, 2),
        "scope_3_kg": round(scope_3_kg, 2),
        "approved_records": approved.count(),
        "pending_records": EmissionRecord.objects.filter(status="pending").count(),
        "flagged_records": EmissionRecord.objects.filter(status="flagged").count(),
    }, status=200)


@require_http_methods(["GET"])
def audit_trail(request, record_id):
    """Get audit log for a specific record."""
    try:
        record = EmissionRecord.objects.get(id=record_id)
    except EmissionRecord.DoesNotExist:
        return JsonResponse({"error": "Record not found"}, status=404)

    logs = record.audit_logs.all().order_by('timestamp')

    data = []
    for log in logs:
        data.append({
            "action": log.action,
            "performed_by": log.performed_by,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "note": log.note,
            "timestamp": log.timestamp.isoformat(),
        })

    return JsonResponse({"record_id": record_id, "audit_log": data}, status=200)


@require_http_methods(["GET"])
def dashboard_stats(request):
    """Get dashboard statistics."""
    total_records = EmissionRecord.objects.count()
    approved_records = EmissionRecord.objects.filter(status="approved").count()
    pending_records = EmissionRecord.objects.filter(status="pending").count()
    flagged_records = EmissionRecord.objects.filter(status="flagged").count()
    rejected_records = EmissionRecord.objects.filter(status="rejected").count()

    total_batches = UploadBatch.objects.count()

    source_breakdown = {}
    for source in ["sap_fuel", "electricity", "travel"]:
        source_breakdown[source] = EmissionRecord.objects.filter(source_type=source).count()

    scope_breakdown = {}
    for scope in ["scope_1", "scope_2", "scope_3"]:
        scope_breakdown[scope] = EmissionRecord.objects.filter(scope=scope).count()

    return JsonResponse({
        "total_records": total_records,
        "approved_records": approved_records,
        "pending_records": pending_records,
        "flagged_records": flagged_records,
        "rejected_records": rejected_records,
        "total_batches": total_batches,
        "source_breakdown": source_breakdown,
        "scope_breakdown": scope_breakdown,
    }, status=200)
