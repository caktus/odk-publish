import pytest

from .factories import (
    CentralServerFactory,
    TemplateVariableFactory,
    ProjectFactory,
    FormTemplateFactory,
    AppUserFormTemplateFactory,
    FormTemplateVersionFactory,
)


class TestCentralServer:
    def test_str(self):
        server = CentralServerFactory.build(base_url="https://live.mycentralserver.com/")
        assert str(server) == "live.mycentralserver.com"


class TestTemplateVariable:
    def test_str(self):
        variable = TemplateVariableFactory.build(name="variable_name")
        assert str(variable) == variable.name


class TestProject:
    def test_str(self):
        project = ProjectFactory.build(name="project", central_id=2)
        assert str(project) == "project (2)"


class TestFormTemplate:
    def test_str(self):
        template = FormTemplateFactory.build(form_id_base="staff_registration", id=2)
        assert str(template) == "staff_registration (2)"

    @pytest.mark.django_db
    def test_get_app_users_no_app_users(self):
        template = FormTemplateFactory.create()
        assert list(template.get_app_users()) == []

    @pytest.mark.django_db
    def test_get_app_users(self):
        template = FormTemplateFactory.create()
        app_user = AppUserFormTemplateFactory.create(form_template=template).app_user
        # other user
        AppUserFormTemplateFactory.create()
        assert list(template.get_app_users()) == [app_user]

    @pytest.mark.django_db
    def test_get_app_users_names(self):
        template = FormTemplateFactory.create()
        app_user = AppUserFormTemplateFactory.create(form_template=template).app_user
        AppUserFormTemplateFactory.create(form_template=template)
        assert template.get_app_users().count() == 2
        assert list(template.get_app_users(names=[app_user.name])) == [app_user]


class TestAppUserFormTemplate:
    def test_xml_form_id(self):
        template = AppUserFormTemplateFactory.build(
            app_user__name="app_user_name", form_template__form_id_base="staff_registration"
        )
        assert template.xml_form_id == "staff_registration_app_user_name"
        assert str(template) == "staff_registration_app_user_name"


class TestFormTemplateVersion:
    def test_str(self):
        version = FormTemplateVersionFactory.build(version="v1")
        assert str(version) == version.file.name
