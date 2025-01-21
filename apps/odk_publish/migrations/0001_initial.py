# Generated by Django 5.1.4 on 2025-01-21 18:01

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AppUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "central_id",
                    models.PositiveIntegerField(
                        help_text="The ID of this app user in ODK Central.",
                        verbose_name="app user ID",
                    ),
                ),
                (
                    "qr_code",
                    models.ImageField(
                        blank=True, null=True, upload_to="qr-codes/", verbose_name="QR Code"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CentralServer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("base_url", models.URLField(max_length=1024)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="FormTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("title_base", models.CharField(max_length=255)),
                ("form_id_base", models.CharField(max_length=255)),
                ("template_url", models.URLField(blank=True, max_length=1024)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AppUserFormTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "app_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_user_forms",
                        to="odk_publish.appuser",
                    ),
                ),
                (
                    "form_template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_user_forms",
                        to="odk_publish.formtemplate",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FormTemplateVersion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("file", models.FileField(upload_to="form-templates/")),
                ("version", models.CharField(max_length=255)),
                (
                    "form_template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="odk_publish.formtemplate",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="form_template_versions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AppUserFormVersion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("file", models.FileField(upload_to="form-templates/")),
                (
                    "app_user_form_template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_user_form_template_versions",
                        to="odk_publish.appuserformtemplate",
                    ),
                ),
                (
                    "form_template_version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_user_form_templates",
                        to="odk_publish.formtemplateversion",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "central_id",
                    models.PositiveIntegerField(
                        help_text="The ID of this project in ODK Central.",
                        verbose_name="project ID",
                    ),
                ),
                (
                    "central_server",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projects",
                        to="odk_publish.centralserver",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="formtemplate",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="form_templates",
                to="odk_publish.project",
            ),
        ),
        migrations.AddField(
            model_name="appuser",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="app_users",
                to="odk_publish.project",
            ),
        ),
        migrations.CreateModel(
            name="TemplateVariable",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "name",
                    models.CharField(
                        max_length=255,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Name must start with a letter or underscore and contain no spaces.",
                                regex="^[A-Za-z_][A-Za-z0-9_]*$",
                            )
                        ],
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("name",), name="unique_template_variable_name")
                ],
            },
        ),
        migrations.AddField(
            model_name="project",
            name="template_variables",
            field=models.ManyToManyField(
                blank=True, related_name="projects", to="odk_publish.templatevariable"
            ),
        ),
        migrations.CreateModel(
            name="AppUserTemplateVariable",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("value", models.CharField(max_length=1024)),
                (
                    "app_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_user_template_variables",
                        to="odk_publish.appuser",
                    ),
                ),
                (
                    "template_variable",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_users_through",
                        to="odk_publish.templatevariable",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="appuser",
            name="template_variables",
            field=models.ManyToManyField(
                blank=True,
                related_name="app_users",
                through="odk_publish.AppUserTemplateVariable",
                to="odk_publish.templatevariable",
            ),
        ),
        migrations.AddConstraint(
            model_name="appuserformtemplate",
            constraint=models.UniqueConstraint(
                fields=("app_user", "form_template"), name="unique_app_user_form_template"
            ),
        ),
        migrations.AddConstraint(
            model_name="formtemplateversion",
            constraint=models.UniqueConstraint(
                fields=("form_template", "version"), name="unique_form_template_version"
            ),
        ),
        migrations.AddConstraint(
            model_name="appuserformversion",
            constraint=models.UniqueConstraint(
                fields=("app_user_form_template", "form_template_version"),
                name="unique_app_user_form_template_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="appusertemplatevariable",
            constraint=models.UniqueConstraint(
                fields=("app_user", "template_variable"), name="unique_app_user_template_variable"
            ),
        ),
        migrations.AddConstraint(
            model_name="appuser",
            constraint=models.UniqueConstraint(
                fields=("project", "name"), name="unique_project_name"
            ),
        ),
    ]
