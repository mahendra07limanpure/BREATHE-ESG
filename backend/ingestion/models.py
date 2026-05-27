from django.db import models
from django.db.models import Sum


# ─────────────────────────────────────────────
# TABLE 1: UploadBatch
# Tracks which file each row came from and when
# ─────────────────────────────────────────────
class UploadBatch(models.Model):

    SOURCE_CHOICES = [
        ("sap_fuel",    "SAP Fuel & Procurement"),
        ("electricity", "Electricity"),
        ("travel",      "Corporate Travel"),
    ]

    source_type  = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    file_name    = models.CharField(max_length=255)
    uploaded_by  = models.CharField(max_length=255, default="analyst")
    uploaded_at  = models.DateTimeField(auto_now_add=True)
    total_rows   = models.IntegerField(default=0)
    flagged_rows = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.source_type} — {self.file_name}"


# ─────────────────────────────────────────────
# TABLE 2: EmissionRecord   ← CORE TABLE
# One row per line of ingested CSV data
# ─────────────────────────────────────────────
class EmissionRecord(models.Model):

    SOURCE_CHOICES = [
        ("sap_fuel",    "SAP Fuel & Procurement"),
        ("electricity", "Electricity"),
        ("travel",      "Corporate Travel"),
    ]

    SCOPE_CHOICES = [
        ("scope_1", "Scope 1 — Direct fuel combustion"),
        ("scope_2", "Scope 2 — Purchased electricity"),
        ("scope_3", "Scope 3 — Business travel"),
    ]

    STATUS_CHOICES = [
        ("pending",  "Pending review"),
        ("flagged",  "Flagged — needs attention"),
        ("approved", "Approved — locked for audit"),
        ("rejected", "Rejected — excluded from totals"),
    ]

    # ── Where this row came from ──────────────
    upload_batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        related_name="records",
        null=True
    )
    source_type  = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    scope        = models.CharField(max_length=10, choices=SCOPE_CHOICES)

    # ── What the activity was ─────────────────
    activity_type = models.CharField(max_length=255)  # diesel / electricity / flight
    site_name     = models.CharField(max_length=255, blank=True)
    record_date   = models.DateField()

    # ── Raw values exactly as in the CSV ─────
    quantity_raw = models.FloatField()
    unit_raw     = models.CharField(max_length=50)   # GAL, LTRS, kVAh — as uploaded

    # ── After your parser normalises them ────
    quantity_normalised = models.FloatField()
    unit_normalised     = models.CharField(max_length=50)  # L, kWh, km — standard

    # ── CO2 calculation ───────────────────────
    emission_factor = models.FloatField()   # kg CO2 per normalised unit
    co2_kg          = models.FloatField()   # quantity_normalised × emission_factor

    # ── Review status ─────────────────────────
    status      = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    flag_reason = models.TextField(blank=True, null=True)
    is_locked   = models.BooleanField(default=False)

    # ── Original row kept for traceability ───
    raw_data   = models.JSONField()
    row_hash   = models.CharField(
        max_length=64,
        db_index=True,
        default='',
        help_text='MD5 hash for duplicate detection'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.source_type} | {self.activity_type} | {self.record_date} | {self.status}"

    # ── Approve / Reject actions ──────────────
    def approve(self, performed_by="analyst", note=""):
        """Approve record and create audit entry."""
        self.status    = "approved"
        self.is_locked = True
        self.save()

        AuditLog.objects.create(
            record       = self,
            action       = "approved",
            performed_by = performed_by,
            old_value    = "pending" if self.flag_reason else "pending",
            new_value    = "approved",
            note         = note or "Analyst approved record",
        )

    def reject(self, performed_by="analyst", note=""):
        """Reject record and create audit entry."""
        old_status = self.status
        self.status = "rejected"
        self.save()

        AuditLog.objects.create(
            record       = self,
            action       = "rejected",
            performed_by = performed_by,
            old_value    = old_status,
            new_value    = "rejected",
            note         = note or "Analyst rejected record",
        )

    def edit_field(self, field_name, new_value, performed_by="analyst", note=""):
        """Edit a field and create audit entry. Locked records cannot be edited."""
        if self.is_locked:
            raise ValueError("Cannot edit a locked/approved record")

        old_value = getattr(self, field_name, None)
        setattr(self, field_name, new_value)
        self.save()

        AuditLog.objects.create(
            record       = self,
            action       = "edited",
            performed_by = performed_by,
            old_value    = str(old_value),
            new_value    = str(new_value),
            note         = note or f"Edited {field_name}",
        )


# ─────────────────────────────────────────────
# TABLE 3: AuditLog
# Insert-only — every approve/reject/edit logged
# ─────────────────────────────────────────────
class AuditLog(models.Model):

    ACTION_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("edited",   "Edited"),
        ("flagged",  "Auto-flagged on ingest"),
    ]

    record       = models.ForeignKey(
        EmissionRecord,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )
    action       = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.CharField(max_length=255, default="analyst")
    old_value    = models.TextField(blank=True, null=True)
    new_value    = models.TextField(blank=True, null=True)
    note         = models.TextField(blank=True)
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.action} on #{self.record_id} at {self.timestamp}"


# ─────────────────────────────────────────────
# TABLE 4: PlantMaster
# SAP WERKS code → readable site name
# ─────────────────────────────────────────────
class PlantMaster(models.Model):
    werks     = models.CharField(max_length=10, unique=True)
    site_name = models.CharField(max_length=255)
    city      = models.CharField(max_length=100, blank=True)
    state     = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.werks} → {self.site_name}"