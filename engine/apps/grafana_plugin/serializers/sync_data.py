from typing import Dict, List

from rest_framework import serializers
from dataclasses import asdict

from apps.grafana_plugin.sync_data import SyncPermission

"""

@dataclass
class SyncData:
    users: List[SyncUser]
    teams: List[SyncTeam]
    team_members: Dict[int, List[int]]
    config: SyncFeaturesConfig
"""


class SyncPermissionSerializer(serializers.Serializer):
    action = serializers.CharField()

    def create(self, validated_data):
        return SyncPermission(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)


class SyncUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    login = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    avatar_url = serializers.URLField()
    permissions = SyncPermissionSerializer(many=True)
    teams = serializers.ListField(child=serializers.IntegerField(), required=False)

    def create(self, validated_data):
        return SyncPermission(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)


class SyncTeamSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    avatar_url = serializers.URLField()

    def create(self, validated_data):
        return SyncPermission(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)


class TeamMemberMappingField(serializers.Field):
    def to_representation(self, value: Dict[int, List[int]]):
        return {str(k): v for k, v in value.items()}

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Expected a dictionary")
        try:
            return {int(k): v for k, v in data.items()}
        except ValueError:
            raise serializers.ValidationError("All keys must be convertible to integers")


class SyncFeaturesConfigSerializer(serializers.Serializer):
    stack_id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    license = serializers.CharField()
    grafana_url = serializers.URLField()
    grafana_token = serializers.CharField()
    rbac_enabled = serializers.BooleanField()
    incident_enabled = serializers.BooleanField()
    incident_backend_url = serializers.URLField()
    labels_enabled = serializers.BooleanField()

    def create(self, validated_data):
        return SyncPermission(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)


class SyncDataSerializer(serializers.Serializer):
    users = serializers.ListField(child=SyncUserSerializer())
    teams = serializers.ListField(child=SyncTeamSerializer())
    team_members = TeamMemberMappingField()
    config = SyncFeaturesConfigSerializer()

    def create(self, validated_data):
        return SyncPermission(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)
