from emoji import emojize
from rest_framework import serializers

from apps.base.models import OrganizationLogRecord
from common.api_helpers.mixins import EagerLoadingMixin


class OrganizationLogRecordSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    author = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationLogRecord
        fields = [
            "id",
            "author",
            "created_at",
            "description",
            "labels",
        ]

        read_only_fields = fields.copy()

    PREFETCH_RELATED = [
        "author__organization",
        # "author__slack_user_identities__slack_team_identity__amixr_team",
    ]

    SELECT_RELATED = ["author", "organization"]

    def get_author(self, obj):
        if obj.author:
            user_data = obj.author.short()
            return user_data

    def get_description(self, obj):
        return emojize(obj.description, use_aliases=True).replace("\n", "<br>")
