import logging
from urllib.parse import urljoin

import requests
from django.db import models, transaction

from apps.base.utils import live_settings
from apps.oss_installation.models import CloudHeartbeat
from apps.oss_installation.models.cloud_user_identity import CloudUserIdentity
from apps.user_management.models import User
from settings.base import GRAFANA_CLOUD_ONCALL_API_URL

logger = logging.getLogger(__name__)


class CloudConnector(models.Model):
    """
    CloudOrganizationConnector model represents connection between oss organization and cloud organization.
    """

    cloud_url = models.URLField()
    # organization = models.OneToOneField(
    #     "user_management.organization", related_name="cloud_connector", on_delete=models.CASCADE
    # )

    @classmethod
    def sync_with_cloud(cls, token=None):
        """
        sync_with_cloud sync organization with cloud organization defined by provided GRAFANA_CLOUD_ONCALL_TOKEN.
        """
        sync_status = False
        error_msg = None

        api_token = token or live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
            error_msg = "GRAFANA_CLOUD_ONCALL_TOKEN is not set"
        else:
            info_url = urljoin(GRAFANA_CLOUD_ONCALL_API_URL, "api/v1/info/")
            try:
                r = requests.get(info_url, headers={"AUTHORIZATION": api_token}, timeout=5)
                if r.status_code == 200:
                    connector = cls.objects.get_or_create()
                    connector.cloud_url = r.json()["url"]
                    connector.save()
                elif r.status_code == 403:
                    logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is invalid")
                    error_msg = "Invalid token"
                else:
                    error_msg = f"Non-200 HTTP code. Got {r.status_code}"
            except requests.exceptions.RequestException as e:
                logger.warning(f"Unable to sync with cloud. Request exception {str(e)}")
                error_msg = f"Unable to sync with cloud"

        return sync_status, error_msg

    def sync_users_with_cloud(self) -> tuple[bool, str]:
        sync_status = False
        error_msg = None

        api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
            error_msg = "GRAFANA_CLOUD_ONCALL_TOKEN is not set"

        existing_emails = list(User.objects.values_list("email", flat=True))
        matching_users = []
        users_url = urljoin(GRAFANA_CLOUD_ONCALL_API_URL, "api/v1/users")

        fetch_next_page = True
        users_fetched = True
        page = 1
        while fetch_next_page:
            try:
                url = urljoin(users_url, f"?page={page}&?short=true")
                r = requests.get(url, headers={"AUTHORIZATION": api_token}, timeout=5)
                if r.status_code != 200:
                    logger.warning(
                        f"Unable to fetch page {page} while sync_users_with_cloud. Response status code {r.status_code}"
                    )
                    error_msg = f"Non-200 HTTP code. Got {r.status_code}"
                    users_fetched = False
                    break
                data = r.json()
                matching_users.extend(list(filter(lambda u: (u["email"] in existing_emails), data["results"])))
                page += 1
                if data["next"] is None:
                    fetch_next_page = False
            except requests.exceptions.RequestException as e:
                logger.warning(f"Unable to sync users with cloud. Request exception {str(e)}")
                error_msg = f"Unable to sync with cloud"
                users_fetched = False
                break

        if users_fetched:
            with transaction.atomic():
                cloud_users_identities_to_create = []
                for user in matching_users:
                    cloud_users_identities_to_create.append(
                        CloudUserIdentity(
                            cloud_id=user["id"],
                            email=user["email"],
                            phone_number_verified=user["is_phone_number_verified"],
                        )
                    )

                CloudUserIdentity.objects.delete()
                CloudUserIdentity.objects.bulk_create(cloud_users_identities_to_create, batch_size=1000)

        return sync_status, error_msg

    def sync_user_with_cloud(self, user):
        sync_status = False
        error_msg = None

        api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning(f"Unable to sync_user_with cloud user_id {user.id}. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
            error_msg = "GRAFANA_CLOUD_ONCALL_TOKEN is not set"
        else:
            url = urljoin(GRAFANA_CLOUD_ONCALL_API_URL, f"api/v1/users/?email={user.email}")
            try:
                r = requests.get(url, headers={"AUTHORIZATION": api_token}, timeout=5)
                if r.status_code != 200:
                    logger.warning(
                        f"Unable to sync_user_with_cloud user_id {user.id}. Response status code {r.status_code}"
                    )
                    error_msg = f"Non-200 HTTP code. Got {r.status_code}"
                else:
                    data = r.json()
                    if len(data["results"]) != 0:
                        cloud_used_data = data["results"][0]
                        with transaction.atomic():
                            CloudUserIdentity.objects.filter(email=user.emai).delete()
                            CloudUserIdentity.objects.create(
                                email=user.email,
                                phone_number_verified=cloud_used_data["is_phone_number_verified"],
                                cloud_id=cloud_used_data["id"],
                            )
                        sync_status = True
                    else:
                        logger.warning(
                            f"Unable to sync_user_with_cloud user_id {user.id}. User with {user.email} not found"
                        )
                        error_msg = f"User with email not found {user.email}"
            except requests.exceptions.RequestException as e:
                logger.warning(f"Unable to sync_user_with cloud user_id {user.id}. Request exception {str(e)}")
                error_msg = f"Unable to sync with cloud"

        return sync_status, error_msg

    @classmethod
    def remove_sync(cls):
        cls.objects.delete()
        CloudUserIdentity.objects.delete()
        CloudHeartbeat.objects.delete()
