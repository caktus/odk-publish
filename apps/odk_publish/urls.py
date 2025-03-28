from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "odk_publish"
urlpatterns = [
    path(
        "o/<slug:organization_slug>/",
        login_required(TemplateView.as_view(template_name="home.html")),
        name="organization-home",
    ),
    path(
        "o/<slug:organization_slug>/servers/sync/",
        views.server_sync,
        name="server-sync",
    ),
    path(
        "servers/sync/projects/",
        views.server_sync_projects,
        name="server-sync-projects",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/app-users/",
        views.app_user_list,
        name="app-user-list",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/app-users/<int:app_user_pk>/",
        views.app_user_detail,
        name="app-user-detail",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/app-users/generate-qr-codes/",
        views.app_user_generate_qr_codes,
        name="app-users-generate-qr-codes",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/app-users/export/",
        views.app_user_export,
        name="app-users-export",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/app-users/import/",
        views.app_user_import,
        name="app-users-import",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/form-templates/",
        views.form_template_list,
        name="form-template-list",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/form-templates/<int:form_template_id>/",
        views.form_template_detail,
        name="form-template-detail",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/form-templates/<int:form_template_id>/publish/",
        views.form_template_publish,
        name="form-template-publish",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/form-templates/add/",
        views.change_form_template,
        name="add-form-template",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/form-templates/<int:form_template_id>/edit/",
        views.change_form_template,
        name="edit-form-template",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/app-users/add/",
        views.change_app_user,
        name="add-app-user",
    ),
    path(
        "o/<slug:organization_slug>/<int:odk_project_pk>/app-users/<int:app_user_id>/edit/",
        views.change_app_user,
        name="edit-app-user",
    ),
    path("create-organization/", views.create_organization, name="create-organization"),
]
