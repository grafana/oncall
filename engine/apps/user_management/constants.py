import typing

from django.db.models import TextChoices

from apps.user_management.types import AlertGroupTableColumn


class AlertGroupTableDefaultColumnChoices(TextChoices):
    STATUS = "status", "Status"
    ID = "id", "ID"
    TITLE = "title", "Title"
    ALERTS = "alerts", "Alerts"
    INTEGRATION = "integration", "Integration"
    CREATED = "created", "Created"
    LABELS = "labels", "Labels"
    TEAM = "team", "Team"
    USERS = "users", "Users"


class AlertGroupTableColumnTypeChoices(TextChoices):
    DEFAULT = "default"
    LABEL = "label"


def default_columns() -> typing.List[AlertGroupTableColumn]:
    return [
        {"name": column.label, "id": column.value, "type": AlertGroupTableColumnTypeChoices.DEFAULT.value}
        for column in AlertGroupTableDefaultColumnChoices
    ]
