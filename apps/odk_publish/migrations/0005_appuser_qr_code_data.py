# Generated by Django 5.1.5 on 2025-03-06 01:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("odk_publish", "0004_merge_20250305_0935"),
    ]

    operations = [
        migrations.AddField(
            model_name="appuser",
            name="qr_code_data",
            field=models.JSONField(blank=True, null=True, verbose_name="QR Code data"),
        ),
    ]
