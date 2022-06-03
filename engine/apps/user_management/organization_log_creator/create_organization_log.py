from django.apps import apps


def create_organization_log(organization, author, type, description):
    OrganizationLogRecord = apps.get_model("base", "OrganizationLogRecord")
    OrganizationLogRecord.objects.create(
        organization=organization,
        author=author,
        type=type,
        description=description,
    )
