from urllib.parse import urljoin

from rest_framework import serializers

import apps.oss_installation.constants as cloud_constants
from apps.oss_installation.models import CloudConnector, CloudUserIdentity
from apps.user_management.models import User


class CloudUserSerializer(serializers.ModelSerializer):
    cloud_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["cloud_data"]

    def get_cloud_data(self, obj):
        link = None
        status = cloud_constants.CLOUD_NOT_SYNCED
        connector = CloudConnector.objects.filter().first()
        if connector is not None:
            cloud_user_identity = CloudUserIdentity.objects.filter(email=obj.email).first()
            if cloud_user_identity is None:
                status = cloud_constants.CLOUD_SYNCED_USER_NOT_FOUND
                link = connector.cloud_url
            elif not cloud_user_identity.phone_number_verified:
                status = cloud_constants.CLOUD_SYNCED_USER_NOT_FOUND
                link = urljoin(
                    connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={cloud_user_identity.cloud_id}"
                )
            else:
                status = cloud_constants.CLOUD_SYNCED_PHONE_VERIFIED
                link = urljoin(
                    connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={cloud_user_identity.cloud_id}"
                )
        cloud_data = {"status": status, "link": link}
        return cloud_data
