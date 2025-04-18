import pytest
from django.urls import reverse
from django.conf import settings

from tests.odk_publish.factories import (
    FormTemplateFactory,
    OrganizationFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestChangeFormTemplate:
    @pytest.fixture
    def user(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        user.save()
        client.force_login(user=user)
        return user

    @pytest.fixture
    def form_template(self):
        return FormTemplateFactory()

    @pytest.fixture
    def url(self, form_template):
        return reverse(
            "odk_publish:edit-form-template",
            kwargs={
                "organization_slug": form_template.project.organization.slug,
                "odk_project_pk": form_template.project_id,
                "form_template_id": form_template.id,
            },
        )

    def test_get(self, client, url, user, form_template):
        urls = [
            reverse("admin:odk_publish_formtemplate_add"),
            reverse("admin:odk_publish_formtemplate_change", args=[form_template.id]),
        ]
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200
            # Ensure the context includes the variables required for the Google Picker JS
            for var in ("google_client_id", "google_api_key", "google_app_id"):
                assert response.context[var] == getattr(settings, var.upper())
            assert response.context["google_scopes"] == " ".join(
                settings.SOCIALACCOUNT_PROVIDERS["google"]["SCOPE"]
            )
            # Ensure the 'Cross-Origin-Opener-Policy' header has the value required
            # for the Google Picker popup to work correctly
            assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin-allow-popups"


@pytest.mark.django_db
class TestOrganizationInvitationAdminAdd:
    @pytest.fixture
    def user(self, client):
        user = UserFactory(is_staff=True, is_superuser=True)
        user.save()
        client.force_login(user=user)
        return user

    @pytest.fixture
    def url(self):
        return reverse("admin:odk_publish_organizationinvitation_add")

    def valid_form(self, client, url, organization, data, mailoutbox):
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        # Ensure the expected OrganizationInvitation is created in the DB
        qs = organization.organizationinvitation_set.filter(email=data["email"])
        assert qs.count() == 1
        invitation = qs.get()
        if data.get("inviter"):
            assert invitation.inviter.id == data["inviter"]
        else:
            assert invitation.inviter is None
        assert not invitation.accepted
        assert invitation.sent is not None
        assert not invitation.key_expired()
        # Ensure an invitation email was sent
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [data["email"]]

    def test_valid_form(self, client, url, user, mailoutbox):
        organization = OrganizationFactory()
        data = {
            "email": "test@test.com",
            "organization": organization.id,
        }
        self.valid_form(client, url, organization, data, mailoutbox)

    def test_valid_form_with_inviter(self, client, url, user, mailoutbox):
        organization = OrganizationFactory()
        data = {
            "email": "test@test.com",
            "organization": organization.id,
            "inviter": user.id,
        }
        self.valid_form(client, url, organization, data, mailoutbox)
