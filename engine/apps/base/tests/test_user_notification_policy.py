import pytest
from django.utils.timezone import timedelta

from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import (
    NotificationChannelAPIOptions,
    NotificationChannelOptions,
    NotificationChannelPublicAPIOptions,
    validate_channel_choice,
)
from apps.base.tests.messaging_backend import TestOnlyBackend
from common.exceptions import UserNotificationPolicyCouldNotBeDeleted


@pytest.mark.parametrize(
    "notification_type,kwargs, expected_verbal",
    [
        (
            UserNotificationPolicy.Step.WAIT,
            {
                "wait_delay": timedelta(minutes=5),
            },
            "5 min",
        ),
        (UserNotificationPolicy.Step.NOTIFY, {"notify_by": UserNotificationPolicy.NotificationChannel.SLACK}, "Slack"),
        (UserNotificationPolicy.Step.WAIT, {}, "0 min"),
        (None, {}, "Not set"),
    ],
)
@pytest.mark.django_db
def test_short_verbal(
    make_organization,
    make_user_for_organization,
    make_user_notification_policy,
    notification_type,
    kwargs,
    expected_verbal,
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    policy = make_user_notification_policy(user, notification_type, **kwargs)
    assert policy.short_verbal == expected_verbal


@pytest.mark.django_db
def test_short_verbals_for_user(
    make_organization,
    make_user_for_organization,
    make_user_notification_policy,
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    make_user_notification_policy(
        user, UserNotificationPolicy.Step.NOTIFY, notify_by=UserNotificationPolicy.NotificationChannel.SLACK
    )

    make_user_notification_policy(user, UserNotificationPolicy.Step.WAIT, wait_delay=timedelta(minutes=5))

    make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
        important=True,
    )

    expected = (("Slack", "5 min"), ("SMS",))
    assert UserNotificationPolicy.get_short_verbals_for_user(user) == expected


@pytest.mark.django_db
def test_extra_messaging_backends_details():
    assert TestOnlyBackend.backend_id in UserNotificationPolicy.NotificationChannel.names
    assert TestOnlyBackend.backend_id not in NotificationChannelOptions.AVAILABLE_FOR_USE
    channel_choice = getattr(UserNotificationPolicy.NotificationChannel, TestOnlyBackend.backend_id)
    assert NotificationChannelAPIOptions.LABELS[channel_choice] == "Test Only Backend"
    assert NotificationChannelAPIOptions.SHORT_LABELS[channel_choice] == TestOnlyBackend.short_label
    assert NotificationChannelPublicAPIOptions.LABELS[channel_choice] == "notify_by_{}".format(
        TestOnlyBackend.backend_id.lower()
    )

    assert validate_channel_choice(channel_choice) is None


@pytest.mark.django_db
def test_unable_to_delete_last_notification_policy(
    make_organization,
    make_user_for_organization,
    make_user_notification_policy,
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    first_policy = make_user_notification_policy(
        user, UserNotificationPolicy.Step.NOTIFY, notify_by=UserNotificationPolicy.NotificationChannel.SLACK
    )

    second_policy = make_user_notification_policy(
        user, UserNotificationPolicy.Step.WAIT, wait_delay=timedelta(minutes=5)
    )

    first_policy.delete()
    with pytest.raises(UserNotificationPolicyCouldNotBeDeleted):
        second_policy.delete()
