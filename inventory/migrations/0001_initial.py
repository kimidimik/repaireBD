from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Part",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=100, unique=True, verbose_name="Code")),
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("current_stock", models.PositiveIntegerField(default=0, verbose_name="Current stock")),
                ("reserved", models.PositiveIntegerField(default=0, verbose_name="Reserved")),
                ("min_stock", models.PositiveIntegerField(default=0, verbose_name="Minimum stock")),
                (
                    "price",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Price"),
                ),
                ("supplier", models.CharField(blank=True, max_length=255, verbose_name="Supplier")),
            ],
            options={"verbose_name": "Part", "verbose_name_plural": "Parts"},
        )
    ]
