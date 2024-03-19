import typing

from django.db.models import TextChoices


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


class AlertGroupTableColumn(typing.TypedDict):
    id: str
    name: str
    type: str


class AlertGroupTableColumns(typing.TypedDict):
    visible: typing.List[AlertGroupTableColumn]
    hidden: typing.List[AlertGroupTableColumn]
    default: bool


def default_columns() -> typing.List[AlertGroupTableColumn]:
    return [
        {"name": column.label, "id": column.value, "type": AlertGroupTableColumnTypeChoices.DEFAULT.value}
        for column in AlertGroupTableDefaultColumnChoices
    ]


class GoogleCalendarSettings(typing.TypedDict):
    create_shift_swaps_automatically: bool
    specific_oncall_schedules_to_sync: typing.Optional[typing.List[str]]
    """
    `public_primary_key` of specific OnCall schedules that should be considering for automatic shift swap creation.
    """
