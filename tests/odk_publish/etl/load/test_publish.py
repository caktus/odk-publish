import datetime as dt

import boto3
import pytest
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from gspread.utils import ExportFormat
from moto import mock_aws

from apps.odk_publish.etl.load import (
    PublishTemplateEvent,
    publish_form_template,
    get_attachment_paths,
)
from apps.odk_publish.etl.odk.publish import ProjectAppUserAssignment
from tests.odk_publish.factories import (
    AppUserFormTemplateFactory,
    FormTemplateFactory,
    ProjectAttachmentFactory,
    ProjectFactory,
)
from tests.users.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="function")
def s3_storage(request, settings):
    """If `request.param` is True, override the default storage backend to use S3
    and mock all S3 interactions.
    """
    if request.param:
        # Override S3 settings
        settings.AWS_ACCESS_KEY_ID = "testing"
        settings.AWS_SECRET_ACCESS_KEY = "testing"
        settings.AWS_STORAGE_BUCKET_NAME = "testing"

        with mock_aws():
            # Create the S3 bucket
            conn = boto3.resource("s3", region_name=settings.AWS_S3_REGION_NAME)
            conn.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            # Override the default storage before the test is run
            original_default_backend = settings.STORAGES["default"]["BACKEND"]
            settings.STORAGES |= {"default": {"BACKEND": "config.storages.MediaBoto3Storage"}}
            yield
            # Undo the storage change after the test is run
            settings.STORAGES |= {"default": {"BACKEND": original_default_backend}}
    else:
        # Do nothing
        yield


class TestPublishFormTemplate:
    """Test full publish_form_template function."""

    def send_message(self, message: str, complete: bool = False):
        pass

    @pytest.mark.parametrize("s3_storage", [False, True], indirect=True)
    def test_publish(self, mocker, requests_mock, settings, s3_storage):
        using_s3_storage = (
            settings.STORAGES["default"]["BACKEND"] == "config.storages.MediaBoto3Storage"
        )
        project = ProjectFactory(central_server__base_url="https://central", central_id=2)
        form_template = FormTemplateFactory(project=project, form_id_base="staff_registration")
        # Create 2 app users
        user_form1 = AppUserFormTemplateFactory(form_template=form_template, app_user__name="user1")
        user_form2 = AppUserFormTemplateFactory(form_template=form_template, app_user__name="user2")
        event = PublishTemplateEvent(form_template=form_template.id, app_users=["user1"])
        # Create 2 static attachments. Since `render_template_for_app_user` is mocked,
        # `set_survey_attachments` will not actually be called, so both attachments
        # should be included in the call to `create_or_update_form()`
        attachments = ProjectAttachmentFactory.create_batch(2, project=project)
        if using_s3_storage:
            # Paths passed to `create_or_update_form` should be local temp file paths
            expected_attachment_paths = [storages["temp"].path(i.name) for i in attachments]
        else:
            expected_attachment_paths = [i.file.path for i in attachments]
        # Mock Gspread download
        mock_gspread_client = mocker.patch("apps.odk_publish.etl.google.gspread_client")
        mock_gspread_client.return_value.open_by_url.return_value.export.return_value = (
            b"file content"
        )
        # Mock rendering the template
        mock_file = SimpleUploadedFile(
            "myform.xlsx", b"file content", content_type=ExportFormat.EXCEL
        )
        mocker.patch(
            "apps.odk_publish.etl.transform.render_template_for_app_user", return_value=mock_file
        )
        # Mock the ODK Central client
        mock_get_version = mocker.patch(
            "apps.odk_publish.etl.odk.publish.PublishService.get_unique_version_by_form_id",
            return_value="2025-02-01-v1",
        )

        assignments = {
            "user1": ProjectAppUserAssignment(
                projectId=project.central_id,
                id=user_form1.app_user.central_id,
                type="field_key",
                displayName="user1",
                createdAt=dt.datetime.now(),
                updatedAt=None,
                deletedAt=None,
                token="token1",
                xml_form_ids=["staff_registration_user1"],
            ),
            "user2": ProjectAppUserAssignment(
                projectId=project.central_id,
                id=user_form2.app_user.central_id,
                type="field_key",
                displayName="user2",
                createdAt=dt.datetime.now(),
                updatedAt=None,
                deletedAt=None,
                token="token1",
                xml_form_ids=["staff_registration_user2"],
            ),
        }
        mock_get_users = mocker.patch(
            "apps.odk_publish.etl.odk.publish.PublishService.get_or_create_app_users",
            return_value=assignments,
        )
        mock_create_or_update_form = mocker.patch(
            "apps.odk_publish.etl.odk.publish.PublishService.create_or_update_form",
            return_value=mocker.Mock(),
        )
        mock_assign_app_users_forms = mocker.patch(
            "apps.odk_publish.etl.odk.publish.PublishService.assign_app_users_forms"
        )
        mock_get_attachment_paths = mocker.patch(
            "apps.odk_publish.etl.load.get_attachment_paths", wraps=get_attachment_paths
        )
        publish_form_template(event=event, user=UserFactory(), send_message=self.send_message)
        mock_get_users.assert_called_once()
        mock_get_version.assert_called_once_with(xml_form_id_base=form_template.form_id_base)
        mock_create_or_update_form.assert_has_calls(
            [
                mocker.call(
                    definition=b"file content",
                    xml_form_id=user_form1.xml_form_id,
                    attachments=expected_attachment_paths,
                ),
            ]
        )
        mock_assign_app_users_forms.assert_has_calls(
            [
                mocker.call(app_users=[assignments["user1"]]),
                mocker.call(app_users=[assignments["user2"]]),
            ]
        )
        # `get_attachment_paths` should be called once even if there are 2 app users
        mock_get_attachment_paths.assert_called_once()
        if using_s3_storage:
            # Ensure the temp files were deleted
            for path in expected_attachment_paths:
                assert not storages["temp"].exists(path)
