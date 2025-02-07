import pytest


from apps.odk_publish.etl.odk.client import ODKPublishClient

from django.core.files.uploadedfile import SimpleUploadedFile


from tests.odk_publish.factories import (
    ProjectFactory,
    AppUserFormTemplateFactory,
    FormTemplateVersionFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    return ProjectFactory(central_server__base_url="https://central")


@pytest.fixture
def odk_client(project):
    return ODKPublishClient(base_url="https://central", project_id=project.central_id)


# app_user__project=factory.SelfAttribute("..form_template.project"),


class TestCreateVersions:
    """Test the creation of form template versions before publishing to ODK Central."""

    @pytest.fixture(autouse=True)
    def mock_rendered_template(self, mocker):
        mock_file = SimpleUploadedFile("test.xlsx", b"file content", content_type="text/plain")
        mocker.patch(
            "apps.odk_publish.etl.transform.render_template_for_app_user", return_value=mock_file
        )

    def test_app_user_form_template_create_next_version(self):
        """Given a form template version, test that an app user's version is created."""
        version = FormTemplateVersionFactory(version="v2")
        user_form_template = AppUserFormTemplateFactory(form_template=version.form_template)
        user_form_template.create_next_version(form_template_version=version)
        assert version.form_template.versions.count() == 1
        assert version.form_template.versions.first().version == version.version

    def test_version_create_app_user_versions(self):
        """Test that all app user versions are created."""
        version = FormTemplateVersionFactory(version="v2")
        AppUserFormTemplateFactory.create_batch(size=2, form_template=version.form_template)
        version.create_app_user_versions()
        assert version.app_user_form_templates.count() == 2

    def test_version_create_specific_app_user_versions(self):
        """Test that a limited set of app user versions are created."""
        version = FormTemplateVersionFactory(version="v2")
        assignments = AppUserFormTemplateFactory.create_batch(
            size=2, form_template=version.form_template
        )
        # Create version for only the first assignment
        versions = version.create_app_user_versions(app_users=[assignments[0].app_user])
        assert len(versions) == 1
        assert versions[0].app_user_form_template.app_user == assignments[0].app_user
