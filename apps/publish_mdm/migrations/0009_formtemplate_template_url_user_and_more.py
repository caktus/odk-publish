# Generated by Django 5.1.5 on 2025-03-20 13:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("publish_mdm", "0008_alter_project_template_variables_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="formtemplate",
            name="template_url_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="formtemplate",
            name="form_id_base",
            field=models.CharField(
                help_text="The prefix of the xml_form_id used to identify the form in ODK Central. The App User will be appended to this value.",
                max_length=255,
                verbose_name="Form ID Base",
            ),
        ),
        migrations.AlterField(
            model_name="formtemplate",
            name="template_url",
            field=models.URLField(
                blank=True,
                help_text="The URL of the Google Sheet template. A new version of this sheet will be downloaded for each form publish event.",
                max_length=1024,
                verbose_name="Template URL",
            ),
        ),
        migrations.AlterField(
            model_name="formtemplate",
            name="title_base",
            field=models.CharField(
                help_text="The title to appear in the ODK Collect form list and header of each form page. The App User will be appended to this title.",
                max_length=255,
            ),
        ),
    ]
