from urllib.parse import urlparse

import structlog
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F

from apps.users.models import User

from .etl import template
from .etl.google import download_user_google_sheet
from .etl.odk.config import odk_central_client
from .etl.odk.forms import get_unique_version_by_form_id

logger = structlog.getLogger(__name__)


class AbstractBaseModel(models.Model):
    """Abstract base model for all models in the app"""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class CentralServer(AbstractBaseModel):
    base_url = models.URLField(max_length=1024)

    def __str__(self):
        parsed_url = urlparse(self.base_url)
        return parsed_url.netloc


class TemplateVariable(AbstractBaseModel):
    name = models.CharField(
        max_length=255,
        validators=[
            # https://docs.getodk.org/xlsform/#the-survey-sheet
            RegexValidator(
                regex=r"^[A-Za-z_][A-Za-z0-9_]*$",
                message="Name must start with a letter or underscore and contain no spaces.",
            )
        ],
    )

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="unique_template_variable_name"),
        ]


class Project(AbstractBaseModel):
    name = models.CharField(max_length=255)
    project_id = models.PositiveIntegerField(verbose_name="project ID")
    central_server = models.ForeignKey(
        CentralServer, on_delete=models.CASCADE, related_name="projects"
    )
    template_variables = models.ManyToManyField(
        TemplateVariable, related_name="projects", blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.project_id})"


class FormTemplate(AbstractBaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="form_templates")
    title_base = models.CharField(max_length=255)
    form_id_base = models.CharField(max_length=255)
    template_url = models.URLField(max_length=1024)

    def __str__(self):
        return f"{self.form_id_base} ({self.id})"

    def download_google_sheet(self, user: User, name: str) -> SimpleUploadedFile:
        """Download the Google Sheet Excel file for this form template."""
        social_token = user.get_google_social_token()
        if social_token is None:
            raise ValueError("User does not have a Google social token.")
        return download_user_google_sheet(
            token=social_token.token,
            token_secret=social_token.token_secret,
            sheet_url=self.template_url,
            name=name,
        )

    def create_next_version(self, user: User) -> "FormTemplateVersion":
        """Create the next version of this form template.

        Steps to create the next version:

        1. Query the ODK Central server for this `form_id_base` and increment
           the version number with today's date.
        2. Download the Google Sheet Excel file for this form template.
        3. Create a new FormTemplateVersion instance with the downloaded file.
        """
        with odk_central_client(base_url=self.project.central_server.base_url) as client:
            version = get_unique_version_by_form_id(
                client=client, project_id=self.project.project_id, form_id_base=self.form_id_base
            )
            name = f"{self.form_id_base}-{version}.xlsx"
            file = self.download_google_sheet(user=user, name=name)
            version = FormTemplateVersion.objects.create(
                form_template=self, user=user, file=file, version=version
            )
            version.create_app_user_versions()
            return version


class FormTemplateVersion(AbstractBaseModel):
    form_template = models.ForeignKey(
        FormTemplate, on_delete=models.CASCADE, related_name="versions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="form_template_versions")
    file = models.FileField(upload_to="form-templates/")
    version = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["form_template", "version"], name="unique_form_template_version"
            ),
        ]

    def __str__(self):
        return self.file.name

    def create_app_user_versions(self):
        for app_user_form in AppUserFormTemplate.objects.filter(form_template=self.form_template):
            logger.info("Creating next AppUserFormVersion", app_user_form=app_user_form)
            app_user_form.create_next_version(form_template_version=self)


class AppUserTemplateVariable(AbstractBaseModel):
    app_user = models.ForeignKey(
        "AppUser", on_delete=models.CASCADE, related_name="app_user_template_variables"
    )
    template_variable = models.ForeignKey(
        TemplateVariable, on_delete=models.CASCADE, related_name="app_users_through"
    )
    value = models.CharField(max_length=1024)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["app_user", "template_variable"], name="unique_app_user_template_variable"
            ),
        ]

    def __str__(self):
        return f"{self.value} ({self.id})"


class AppUser(AbstractBaseModel):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="app_users")
    template_variables = models.ManyToManyField(
        through=AppUserTemplateVariable, to=TemplateVariable, related_name="app_users"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "name"], name="unique_project_name"),
        ]

    def __str__(self):
        return self.name

    def get_template_variables(self) -> list[template.TemplateVariable]:
        """Get the template variables and values for this app user."""
        variables = self.app_user_template_variables.annotate(
            name=F("template_variable__name")
        ).values("name", "value")
        return [
            template.TemplateVariable.model_validate(template_variable)
            for template_variable in variables
        ]


class AppUserFormTemplate(AbstractBaseModel):
    app_user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name="app_user_forms")
    form_template = models.ForeignKey(
        FormTemplate, on_delete=models.CASCADE, related_name="app_users"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["app_user", "form_template"], name="unique_app_user_form_template"
            ),
        ]

    def __str__(self):
        return f"{self.app_user} - {self.form_template}"

    def create_next_version(self, form_template_version: FormTemplateVersion):
        from .etl.transform import fill_in_survey_template_variables

        version_file = fill_in_survey_template_variables(
            template=self, version=form_template_version
        )
        return AppUserFormVersion.objects.create(
            app_user_form_template=self,
            form_template_version=form_template_version,
            file=version_file,
        )


class AppUserFormVersion(AbstractBaseModel):
    app_user_form_template = models.ForeignKey(
        AppUserFormTemplate,
        on_delete=models.CASCADE,
        related_name="app_user_form_template_versions",
    )
    form_template_version = models.ForeignKey(
        FormTemplateVersion, on_delete=models.CASCADE, related_name="app_user_form_templates"
    )
    file = models.FileField(upload_to="form-templates/")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["app_user_form_template", "form_template_version"],
                name="unique_app_user_form_template_version",
            ),
        ]

    def __str__(self):
        return f"{self.app_user_form_template} - {self.form_template_version}"
