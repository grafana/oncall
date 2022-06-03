from rest_framework import serializers

from apps.auth_token.models import ApiAuthToken


class PublicApiTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiAuthToken
        fields = [
            "id",
            "name",
            "created_at",
        ]
