from rest_framework import serializers

from apps.oss_installation.models import CloudConnector, CloudUserIdentity
from apps.oss_installation.utils import cloud_user_identity_status
from apps.user_management.models import User


class CloudUserSerializer(serializers.ModelSerializer):
    cloud_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["cloud_data"]

    def get_cloud_data(self, obj):
        connector = CloudConnector.objects.filter().first()
        cloud_user_identity = CloudUserIdentity.objects.filter(email=obj.email).first()
        status, link = cloud_user_identity_status(connector, cloud_user_identity)
        cloud_data = {"status": status, "link": link}
        return cloud_data
