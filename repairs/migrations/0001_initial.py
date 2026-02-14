from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Device",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True, verbose_name="Name")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("is_active", models.BooleanField(default=True, verbose_name="Is active")),
            ],
            options={"verbose_name": "Device", "verbose_name_plural": "Devices"},
        ),
        migrations.CreateModel(
            name="Repair",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateField(auto_now_add=True, verbose_name="Created at")),
                ("serial_number", models.CharField(db_index=True, max_length=50, verbose_name="Serial number")),
                ("defect", models.TextField(verbose_name="Defect")),
                (
                    "repair_difficulty",
                    models.CharField(
                        choices=[
                            ("Test", "Test"),
                            ("Simple", "Simple"),
                            ("Normal", "Normal"),
                            ("Difficult", "Difficult"),
                            ("Very Difficult", "Very Difficult"),
                        ],
                        default="Normal",
                        max_length=32,
                        verbose_name="Repair difficulty",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("New", "New"),
                            ("Awaiting Parts", "Awaiting Parts"),
                            ("In Progress", "In Progress"),
                            ("Completed", "Completed"),
                            ("Closed", "Closed"),
                        ],
                        db_index=True,
                        default="New",
                        max_length=32,
                        verbose_name="Status",
                    ),
                ),
                (
                    "type_of_repair",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Replacement", "Replacement"),
                            ("Cleaning", "Cleaning"),
                            ("Diagnostics", "Diagnostics"),
                            ("Firmware", "Firmware"),
                        ],
                        max_length=32,
                        verbose_name="Type of repair",
                    ),
                ),
                ("note", models.TextField(blank=True, verbose_name="Note")),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="repairs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Technician",
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="repairs.device", verbose_name="Device"
                    ),
                ),
            ],
            options={"verbose_name": "Repair", "verbose_name_plural": "Repairs"},
        ),
        migrations.CreateModel(
            name="RepairPartUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="Quantity")),
                ("date_used", models.DateTimeField(auto_now_add=True, verbose_name="Date used")),
                ("written_off", models.BooleanField(default=False, verbose_name="Written off")),
                (
                    "part",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="inventory.part", verbose_name="Part"
                    ),
                ),
                (
                    "repair",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="part_usages",
                        to="repairs.repair",
                        verbose_name="Repair",
                    ),
                ),
            ],
            options={
                "verbose_name": "Repair part usage",
                "verbose_name_plural": "Repair part usages",
                "unique_together": {("repair", "part")},
            },
        ),
        migrations.AddField(
            model_name="repair",
            name="parts_used",
            field=models.ManyToManyField(related_name="repairs", through="repairs.RepairPartUsage", to="inventory.part"),
        ),
        migrations.AddIndex(model_name="repair", index=models.Index(fields=["serial_number"], name="repairs_rep_serial__f43c99_idx")),
        migrations.AddIndex(model_name="repair", index=models.Index(fields=["status", "created_at"], name="repairs_rep_status_8f25ec_idx")),
    ]
