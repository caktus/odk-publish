import django_tables2 as tables

from .models import FormTemplate


class FormTemplateTable(tables.Table):
    app_users = tables.Column(
        verbose_name="App Users",
        accessor="app_user_count",
        order_by=("app_user_count", "title_base"),
    )
    latest_version = tables.TemplateColumn(
        template_code="{{ record.latest_version.0.version }} <span class='text-gray-400'>({{ record.latest_version.0.user.first_name }})</span>",
        verbose_name="Latest Version",
    )
    publish_next_version = tables.LinkColumn(
        "odk_publish:form-template-list",
        args=[tables.A("pk")],
        text="Publish New Version",
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        model = FormTemplate
        fields = ["title_base", "form_id_base"]
        template_name = "patterns/tables/table.html"
        attrs = {"th": {"scope": "col", "class": "px-4 py-3 whitespace-nowrap "}}
        orderable = False