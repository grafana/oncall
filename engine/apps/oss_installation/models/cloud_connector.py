import logging
import typing
from urllib.parse import urljoin

import requests
from django.db import models, transaction

from apps.base.utils import live_settings
from apps.oss_installation.models.cloud_user_identity import CloudUserIdentity
from apps.user_management.models import User
from common.api_helpers.utils import create_engine_url
from settings.base import GRAFANA_CLOUD_ONCALL_API_URL

logger = logging.getLogger(__name__)


class CloudConnector(models.Model):
    """
    CloudOrganizationConnector model represents connection between oss organization and cloud organization.
    """

    cloud_url = models.URLField()

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
            info_url = create_engine_url("api/v1/info/", override_base=GRAFANA_CLOUD_ONCALL_API_URL)
            try:
                r = requests.get(info_url, headers={"AUTHORIZATION": api_token}, timeout=5)
                if r.status_code == 200:
                    connector, _ = cls.objects.get_or_create()
                    connector.cloud_url = r.json()["url"]
                    connector.save()
                elif r.status_code == 403:
                    logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is invalid")
                    error_msg = "Invalid token"
                else:
                    error_msg = f"Non-200 HTTP code. Got {r.status_code}"
            except requests.exceptions.RequestException as e:
                logger.warning(f"Unable to sync with cloud. Request exception {str(e)}")
                error_msg = "Unable to sync with cloud"

        return sync_status, error_msg

    def sync_users_with_cloud(self) -> typing.Tuple[bool, typing.Optional[str]]:
        sync_status = False
        error_msg = None

        api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning("Unable to sync with cloud. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
            error_msg = "GRAFANA_CLOUD_ONCALL_TOKEN is not set"

        existing_emails = [user.email for user in User.objects.all() if user.is_notification_allowed]
        matching_users = []
        users_url = create_engine_url("api/v1/users", override_base=GRAFANA_CLOUD_ONCALL_API_URL)

        fetch_next_page = True
        users_fetched = True
        page = 1
        while fetch_next_page:
            try:
                url = urljoin(users_url, f"?page={page}&short=true&roles=0&roles=1")
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
                error_msg = "Unable to sync with cloud"
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

                CloudUserIdentity.objects.all().delete()
                CloudUserIdentity.objects.bulk_create(cloud_users_identities_to_create, batch_size=1000)
            sync_status = True
        return sync_status, error_msg

    def sync_user_with_cloud(self, user):
        sync_status = False
        error_msg = None

        api_token = live_settings.GRAFANA_CLOUD_ONCALL_TOKEN
        if api_token is None:
            logger.warning(f"Unable to sync_user_with cloud user_id {user.id}. GRAFANA_CLOUD_ONCALL_TOKEN is not set")
            error_msg = "GRAFANA_CLOUD_ONCALL_TOKEN is not set"
        else:
            url = create_engine_url(
                f"api/v1/users/?email={user.email}&roles=0&roles=1&short=true",
                override_base=GRAFANA_CLOUD_ONCALL_API_URL,
            )
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
                            CloudUserIdentity.objects.filter(email=user.email).delete()
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
                error_msg = "Unable to sync with cloud"

        return sync_status, error_msg

    @classmethod
    def remove_sync(cls):
        from apps.oss_installation.models import CloudHeartbeat

        cls.objects.all().delete()
        CloudUserIdentity.objects.all().delete()
        CloudHeartbeat.objects.all().delete()
