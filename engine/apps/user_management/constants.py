import typing

from django.db.models import IntegerChoices, TextChoices


class AlertGroupTableColumnChoices(IntegerChoices):
    STATUS = 1, "Status"
    ID = 2, "ID"
    TITLE = 3, "Title"
    ALERTS = 4, "Alerts"
    INTEGRATION = 5, "Integration"
    CREATED = 6, "Created"
    LABELS = 7, "Labels"
    TEAM = 8, "Team"
    USERS = 9, "Users"


class AlertGroupTableColumnTypeChoices(TextChoices):
    DEFAULT = "default"
    LABEL = "label"


class AlertGroupTableColumn(typing.TypedDict):
    id: str | int
    name: str
    type: str


class AlertGroupTableColumns(typing.TypedDict):
    visible: typing.List[AlertGroupTableColumn]
    hidden: typing.List[AlertGroupTableColumn]
