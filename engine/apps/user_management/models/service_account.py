import typing
from dataclasses import dataclass

from django.db import models

from apps.user_management.models import Organization

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.user_management.models import Team


@dataclass
class ServiceAccountUser:
    """Authenticated service account in public API requests."""

    service_account: "ServiceAccount"
    organization: "Organization"  # required for insight logs interface
    username: str  # required for insight logs interface
    public_primary_key: str  # required for insight logs interface
    role: str  # required for permissions check
    permissions: typing.List[str]  # required for permissions check

    @property
    def id(self) -> int:
        return self.service_account.id

    @property
    def pk(self) -> int:
        return self.service_account.id

    @property
    def current_team(self) -> None:
        return None

    @property
    def available_teams(self) -> "RelatedManager['Team']":
        return self.organization.teams

    @property
    def organization_id(self) -> int:
        return self.organization.id

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_service_account(self) -> bool:
        return True


class ServiceAccount(models.Model):
    organization: "Organization"

    grafana_id = models.PositiveIntegerField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="service_accounts")
    login = models.CharField(max_length=300)

    class Meta:
        unique_together = ("grafana_id", "organization")

    @property
    def username(self) -> str:
        # required for insight logs interface
        return self.login

    @property
    def public_primary_key(self) -> str:
        # required for insight logs interface
        return f"service-account:{self.grafana_id}"
