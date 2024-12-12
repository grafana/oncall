from dataclasses import asdict
from typing import Dict, List

from rest_framework import serializers

from apps.grafana_plugin.sync_data import SyncData, SyncPermission, SyncSettings, SyncTeam, SyncUser


class SyncPermissionSerializer(serializers.Serializer):
    action = serializers.CharField()

    def create(self, validated_data):
        return SyncPermission(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)


class SyncUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(allow_blank=True)
    login = serializers.CharField()
    email = serializers.CharField()
    role = serializers.CharField()
    avatar_url = serializers.CharField(allow_blank=True)
    permissions = SyncPermissionSerializer(many=True, allow_empty=True, allow_null=True)
    teams = serializers.ListField(child=serializers.IntegerField(), allow_empty=True, allow_null=True)

    def create(self, validated_data):
        return SyncUser(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)


class SyncTeamSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField(allow_blank=True)
    avatar_url = serializers.CharField(allow_blank=True)

    def create(self, validated_data):
        return SyncTeam(**validated_data)

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


class SyncOnCallSettingsSerializer(serializers.Serializer):
    stack_id = serializers.IntegerField()
    org_id = serializers.IntegerField()
    license = serializers.CharField()
    oncall_api_url = serializers.CharField()
    oncall_token = serializers.CharField(allow_blank=True)
    grafana_url = serializers.CharField()
    grafana_token = serializers.CharField()
    rbac_enabled = serializers.BooleanField()
    incident_enabled = serializers.BooleanField()
    incident_backend_url = serializers.CharField(allow_blank=True)
    labels_enabled = serializers.BooleanField()
    irm_enabled = serializers.BooleanField(default=False)

    def validate_grafana_url(self, value):
        # remove trailing slash for URL consistency
        return value.rstrip("/")

    def create(self, validated_data):
        return SyncSettings(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)


class SyncDataSerializer(serializers.Serializer):
    users = serializers.ListField(child=SyncUserSerializer(), allow_null=True, allow_empty=True)
    teams = serializers.ListField(child=SyncTeamSerializer(), allow_null=True, allow_empty=True)
    team_members = TeamMemberMappingField()
    settings = SyncOnCallSettingsSerializer()

    def create(self, validated_data):
        return SyncData(**validated_data)

    def to_representation(self, instance):
        return asdict(instance)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        users = data.get("users")
        if users:

            def create_user(user):
                permissions_data = user.pop("permissions", [])
                permissions = [SyncPermission(**perm) for perm in permissions_data] if permissions_data else []
                return SyncUser(permissions=permissions, **user)

            data["users"] = [create_user(user) for user in users]
        teams = data.get("teams")
        if teams:
            data["teams"] = [SyncTeam(**team) for team in teams]
        settings = data.get("settings")
        if settings:
            data["settings"] = SyncSettings(**settings)
        return data
