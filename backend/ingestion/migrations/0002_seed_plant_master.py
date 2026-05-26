from django.db import migrations


def seed_plant_master(apps, schema_editor):
    PlantMaster = apps.get_model("ingestion", "PlantMaster")

    # Seed values used by the prototype parsers / sample data.
    # MODEL.md documents these mappings for WERKS → site metadata.
    plants = [
        {"werks": "PL01", "site_name": "Mumbai Plant", "city": "Mumbai", "state": "Maharashtra"},
        {"werks": "PL02", "site_name": "Pune Factory", "city": "Pune", "state": "Maharashtra"},
        {"werks": "PL03", "site_name": "Delhi Warehouse", "city": "Delhi", "state": "Delhi"},
        {"werks": "PL04", "site_name": "Gujarat Unit", "city": "Ahmedabad", "state": "Gujarat"},
    ]

    for p in plants:
        PlantMaster.objects.update_or_create(
            werks=p["werks"],
            defaults={
                "site_name": p["site_name"],
                "city": p["city"],
                "state": p["state"],
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("ingestion", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plant_master, migrations.RunPython.noop),
    ]

