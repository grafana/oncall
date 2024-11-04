import datetime
from zoneinfo import ZoneInfo

import pytest
import pytz
from rest_framework import serializers

import common.api_helpers.custom_fields as cf
from common.api_helpers.exceptions import BadRequest


class TestTimeZoneField:
    @pytest.mark.parametrize("tz", pytz.all_timezones)
    def test_valid_timezones(self, tz):
        class MySerializer(serializers.Serializer):
            tz = cf.TimeZoneField()

        try:
            serializer = MySerializer(data={"tz": tz})
            serializer.is_valid(raise_exception=True)

            assert serializer.validated_data["tz"] == tz
        except Exception:
            pytest.fail()

    def test_invalid_timezone(self):
        class MySerializer(serializers.Serializer):
            tz = cf.TimeZoneField()

        with pytest.raises(serializers.ValidationError, match="Invalid timezone"):
            serializer = MySerializer(data={"tz": "potato"})
            serializer.is_valid(raise_exception=True)

    def test_it_works_with_allow_null(self):
        class MySerializer(serializers.Serializer):
            tz = cf.TimeZoneField(allow_null=True)

        try:
            serializer = MySerializer(data={"tz": None})
            serializer.is_valid(raise_exception=True)
            assert serializer.validated_data["tz"] is None

            serializer = MySerializer(data={"tz": "UTC"})
            serializer.is_valid(raise_exception=True)
            assert serializer.validated_data["tz"] == "UTC"
        except Exception:
            pytest.fail()

    def test_it_works_with_required(self):
        class MySerializer(serializers.Serializer):
            tz = cf.TimeZoneField(required=True)

        with pytest.raises(serializers.ValidationError, match="This field is required"):
            serializer = MySerializer(data={})
            serializer.is_valid(raise_exception=True)

        try:
            serializer = MySerializer(data={"tz": "UTC"})
            serializer.is_valid(raise_exception=True)
            assert serializer.validated_data["tz"] == "UTC"
        except Exception:
            pytest.fail()


class TestTimeZoneAwareDatetimeField:
    @pytest.mark.parametrize(
        "test_case,expected_persisted_value",
        [
            # UTC format
            ("2023-07-20T12:00:00Z", datetime.datetime(2023, 7, 20, 12, 0, 0, tzinfo=ZoneInfo("UTC"))),
            # UTC format w/ microseconds
            ("2023-07-20T12:00:00.245652Z", datetime.datetime(2023, 7, 20, 12, 0, 0, 245652, tzinfo=ZoneInfo("UTC"))),
            # UTC offset w/ colons + no microseconds
            ("2023-07-20T12:00:00+07:00", datetime.datetime(2023, 7, 20, 5, 0, 0, tzinfo=ZoneInfo("UTC"))),
            # UTC offset w/ colons + microseconds
            (
                "2023-07-20T12:00:00.245652+07:00",
                datetime.datetime(2023, 7, 20, 5, 0, 0, 245652, tzinfo=ZoneInfo("UTC")),
            ),
            # UTC offset w/ no colons + no microseconds
            ("2023-07-20T12:00:00+0700", datetime.datetime(2023, 7, 20, 5, 0, 0, tzinfo=ZoneInfo("UTC"))),
            # UTC offset w/ no colons + microseconds
            (
                "2023-07-20T12:00:00.245652+0700",
                datetime.datetime(2023, 7, 20, 5, 0, 0, 245652, tzinfo=ZoneInfo("UTC")),
            ),
            ("2023-07-20 12:00:00", None),
            ("20230720T120000Z", None),
        ],
    )
    def test_various_datetimes(self, test_case, expected_persisted_value):
        class MySerializer(serializers.Serializer):
            dt = cf.TimeZoneAwareDatetimeField()

        serializer = MySerializer(data={"dt": test_case})

        if expected_persisted_value:
            serializer.is_valid(raise_exception=True)

            assert serializer.validated_data["dt"] == expected_persisted_value
        else:
            with pytest.raises(serializers.ValidationError):
                serializer.is_valid(raise_exception=True)


class TestSlackChannelsFilteredByOrganizationSlackWorkspaceField:
    class MockRequest:
        def __init__(self, user) -> None:
            self.user = user

    class MySerializer(serializers.Serializer):
        slack_channel_id = cf.SlackChannelsFilteredByOrganizationSlackWorkspaceField()

    @pytest.mark.django_db
    def test_org_does_not_have_slack_connected(
        self,
        make_organization,
        make_user_for_organization,
    ):
        organization = make_organization()
        user = make_user_for_organization(organization)

        serializer = self.MySerializer(
            data={"slack_channel_id": "abcd"},
            context={"request": self.MockRequest(user)},
        )

        with pytest.raises(BadRequest) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert excinfo.value.detail == "Slack isn't connected to this workspace"
        assert excinfo.value.status_code == 400

    @pytest.mark.django_db
    def test_org_channel_doesnt_belong_to_org(
        self,
        make_organization,
        make_user_for_organization,
        make_slack_team_identity,
        make_slack_channel,
    ):
        slack_channel1_id = "FOO"
        slack_channel2_id = "BAR"

        slack_team_identity1 = make_slack_team_identity()
        make_slack_channel(slack_team_identity1, slack_id=slack_channel1_id)

        slack_team_identity2 = make_slack_team_identity()
        make_slack_channel(slack_team_identity2, slack_id=slack_channel2_id)

        organization = make_organization(slack_team_identity=slack_team_identity1)
        user = make_user_for_organization(organization)

        serializer = self.MySerializer(
            data={"slack_channel_id": slack_channel2_id},
            context={"request": self.MockRequest(user)},
        )

        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert excinfo.value.detail == {"slack_channel_id": ["Slack channel does not exist"]}

    @pytest.mark.django_db
    def test_invalid_slack_channel(
        self,
        make_organization,
        make_user_for_organization,
        make_slack_team_identity,
        make_slack_channel,
    ):
        slack_channel_id = "FOO"
        slack_team_identity = make_slack_team_identity()
        make_slack_channel(slack_team_identity, slack_id=slack_channel_id)
        organization = make_organization(slack_team_identity=slack_team_identity)
        user = make_user_for_organization(organization)

        serializer = self.MySerializer(
            data={"slack_channel_id": 1},
            context={"request": self.MockRequest(user)},
        )

        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert excinfo.value.detail == {"slack_channel_id": ["Invalid Slack channel"]}

    @pytest.mark.django_db
    def test_valid(
        self,
        make_organization,
        make_user_for_organization,
        make_slack_team_identity,
        make_slack_channel,
    ):
        slack_channel_id = "FOO"
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity, slack_id=slack_channel_id)
        organization = make_organization(slack_team_identity=slack_team_identity)
        user = make_user_for_organization(organization)

        context = {"request": self.MockRequest(user)}

        serializer = self.MySerializer(data={"slack_channel_id": slack_channel_id}, context=context)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["slack_channel_id"] == slack_channel

        # case insensitive
        serializer = self.MySerializer(data={"slack_channel_id": slack_channel_id.lower()}, context=context)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["slack_channel_id"] == slack_channel


class TestSlackUserGroupsFilteredByOrganizationSlackWorkspaceField:
    class MockRequest:
        def __init__(self, user) -> None:
            self.user = user

    class MySerializer(serializers.Serializer):
        slack_user_group_id = cf.SlackUserGroupsFilteredByOrganizationSlackWorkspaceField()

    @pytest.mark.django_db
    def test_org_does_not_have_slack_connected(
        self,
        make_organization,
        make_user_for_organization,
    ):
        organization = make_organization()
        user = make_user_for_organization(organization)

        serializer = self.MySerializer(
            data={"slack_user_group_id": "abcd"},
            context={"request": self.MockRequest(user)},
        )

        with pytest.raises(BadRequest) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert excinfo.value.detail == "Slack isn't connected to this workspace"
        assert excinfo.value.status_code == 400

    @pytest.mark.django_db
    def test_org_user_group_doesnt_belong_to_org(
        self,
        make_organization,
        make_user_for_organization,
        make_slack_team_identity,
        make_slack_user_group,
    ):
        slack_user_group1_id = "FOO"
        slack_user_group2_id = "BAR"

        slack_team_identity1 = make_slack_team_identity()
        make_slack_user_group(slack_team_identity1, slack_id=slack_user_group1_id)

        slack_team_identity2 = make_slack_team_identity()
        make_slack_user_group(slack_team_identity2, slack_id=slack_user_group2_id)

        organization = make_organization(slack_team_identity=slack_team_identity1)
        user = make_user_for_organization(organization)

        serializer = self.MySerializer(
            data={"slack_user_group_id": slack_user_group2_id},
            context={"request": self.MockRequest(user)},
        )

        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert excinfo.value.detail == {"slack_user_group_id": ["Slack user group does not exist"]}

    @pytest.mark.django_db
    def test_invalid_slack_user_group(
        self,
        make_organization,
        make_user_for_organization,
        make_slack_team_identity,
        make_slack_user_group,
    ):
        slack_user_group_id = "FOO"
        slack_team_identity = make_slack_team_identity()
        make_slack_user_group(slack_team_identity, slack_id=slack_user_group_id)
        organization = make_organization(slack_team_identity=slack_team_identity)
        user = make_user_for_organization(organization)

        serializer = self.MySerializer(
            data={"slack_user_group_id": 1},
            context={"request": self.MockRequest(user)},
        )

        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert excinfo.value.detail == {"slack_user_group_id": ["Invalid Slack user group"]}

    @pytest.mark.django_db
    def test_valid(
        self,
        make_organization,
        make_user_for_organization,
        make_slack_team_identity,
        make_slack_user_group,
    ):
        slack_user_group_id = "FOO"
        slack_team_identity = make_slack_team_identity()
        slack_user_group = make_slack_user_group(slack_team_identity, slack_id=slack_user_group_id)
        organization = make_organization(slack_team_identity=slack_team_identity)
        user = make_user_for_organization(organization)

        context = {"request": self.MockRequest(user)}

        serializer = self.MySerializer(data={"slack_user_group_id": slack_user_group_id}, context=context)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["slack_user_group_id"] == slack_user_group

        # case insensitive
        serializer = self.MySerializer(data={"slack_user_group_id": slack_user_group_id.lower()}, context=context)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["slack_user_group_id"] == slack_user_group
