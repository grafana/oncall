import logging
from urllib.parse import urljoin

import requests
from django.db import models

from apps.base.utils import live_settings
from apps.oss_installation.constants import CLOUD_URL
from apps.oss_installation.models.cloud_user_identity import CloudUserIdentity
from apps.user_management.models import User

logger = logging.getLogger(__name__)


class CloudOrganizationConnector(models.Model):
    """
    CloudOrganizationConnector model represents connection between oss organization and cloud organization.
    """

    cloud_url = models.URLField()
    organization = models.OneToOneField(
        "user_management.organization", related_name="cloud_connector", on_delete=models.CASCADE
    )

    @classmethod
    def sync_with_cloud(cls, organization) -> bool:
        """
        sync_with_cloud sync organization with cloud organization defined by provided GRAFANA_CLOUD_ONCALL_TOKEN.
        """
        sync_status = False

        api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
        else:
            info_url = urljoin(CLOUD_URL, "api/v1/info/")
            try:
                r = requests.get(info_url, headers={"AUTHORIZATION": api_token}, timeout=5)
                if r.status_code == 200:
                    cls.objects.update_or_create(organization=organization, defaults={"cloud_url": r.json()["url"]})
                    sync_status = True
                if r.status_code == 403:
                    logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is invalid")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Unable to sync with cloud. Request exception {str(e)}")
        return sync_status

    def sync_users_with_cloud(self):
        api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
            return

        existing_emails = list(User.objects.filter(organization=self.organization).values_list("email", flat=True))
        # existing_cloud_ids = list(
        #     CloudUserIdentity.objects.filter(organization=self.organization).values_list("cloud_id", flat=True)
        # )
        matching_users = []
        users_url = urljoin(CLOUD_URL, "api/v1/users")

        existing_cloud_identities = list(CloudUserIdentity.objects.filter(organization=self.organization))
        existing_cloud_ids = list(map(lambda identity: identity.cloud_id, existing_cloud_identities))

        fetch_next_page = True
        page = 1
        while fetch_next_page:
            try:
                url = urljoin(users_url, f"?page={page}&?short=true")
                r = requests.get(url, headers={"AUTHORIZATION": api_token}, timeout=5)
                if r.status_code != 200:
                    logger.warning(
                        f"Unable to fetch page {page} while sync_users_with_cloud. Response status code {r.status_code}"
                    )
                    if r.status_code == 429 or r.status_code == 403:
                        break
                data = r.json()
                matching_users.extend(list(filter(lambda u: (u["email"] in existing_emails), data["results"])))
                page += 1
                if data["next"] is None:
                    fetch_next_page = False
            except requests.exceptions.RequestException as e:
                logger.warning(f"Unable to sync users with cloud. Request exception {str(e)}")
                break

        cloud_users_identities_to_update = {}

        cloud_users_identities_to_create = []
        for user in matching_users:
            if user["id"] in existing_cloud_ids:
                cloud_users_identities_to_update[user["id"]] = user
            else:
                cloud_users_identities_to_create.append(
                    CloudUserIdentity(
                        cloud_id=user["id"],
                        email=user["email"],
                        phone_number_verified=user["is_phone_number_verified"],
                        organization=self.organization,
                    )
                )

        for i in existing_cloud_identities:
            i.email = cloud_users_identities_to_update[i.cloud_id]["email"]
            i.phone_number_verified = cloud_users_identities_to_update[i.cloud_id]["is_phone_number_verified"]

        CloudUserIdentity.objects.bulk_create(cloud_users_identities_to_create, batch_size=1000)
        CloudUserIdentity.objects.bulk_update(
            existing_cloud_identities, ["email", "phone_number_verified"], batch_size=1000
        )

    def sync_user_with_cloud(self, user):
        api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning(f"Unable to sync_user_with cloud user_id {user.id}. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
            return

        url = urljoin(CLOUD_URL, f"api/v1/users/?email={user.email}")
        try:
            r = requests.get(url, headers={"AUTHORIZATION": api_token}, timeout=5)
            if r.status_code != 200:
                logger.warning(
                    f"Unable to sync_user_with_cloud user_id {user.id}. Response status code {r.status_code}"
                )
                return
            data = r.json()
            if len(data["results"]) != 0:
                cloud_used_data = data["results"][0]
                CloudUserIdentity.objects.update_or_create(
                    email=user.email,
                    defaults={
                        "phone_number_verified": cloud_used_data["is_phone_number_verified"],
                        "cloud_id": cloud_used_data["id"],
                    },
                )
            else:
                logger.warning(f"Unable to sync_user_with_cloud user_id {user.id}. User with {user.email} not found")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Unable to sync_user_with cloud user_id {user.id}. Request exception {str(e)}")
