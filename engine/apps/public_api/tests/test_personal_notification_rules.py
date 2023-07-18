import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import NotificationChannelPublicAPIOptions

TYPE_WAIT = "wait"


@pytest.fixture()
def personal_notification_rule_public_api_setup(
    make_organization_and_user_with_token,
    make_user_notification_policy,
):
    organization, user, token = make_organization_and_user_with_token()
    notification_rule_wait = make_user_notification_policy(
        user, wait_delay=UserNotificationPolicy.FIVE_MINUTES, step=UserNotificationPolicy.Step.WAIT
    )
    notification_rule_phone_call = make_user_notification_policy(
        user, notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL, step=UserNotificationPolicy.Step.NOTIFY
    )
    notification_rule_important = make_user_notification_policy(
        user,
        notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL,
        step=UserNotificationPolicy.Step.NOTIFY,
        important=True,
    )
    return organization, user, token, notification_rule_wait, notification_rule_phone_call, notification_rule_important


@pytest.mark.django_db
def test_get_personal_notification_rule(personal_notification_rule_public_api_setup):
    _, user, token, _, notification_rule_phone_call, _ = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse(
        "api-public:personal_notification_rules-detail", kwargs={"pk": notification_rule_phone_call.public_primary_key}
    )
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "id": notification_rule_phone_call.public_primary_key,
        "user_id": user.public_primary_key,
        "type": NotificationChannelPublicAPIOptions.LABELS[notification_rule_phone_call.notify_by],
        "position": notification_rule_phone_call.order,
        "important": False,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_personal_notification_rules_list(personal_notification_rule_public_api_setup):
    (
        _,
        user,
        token,
        notification_rule_wait,
        notification_rule_phone_call,
        notification_rule_important,
    ) = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "count": 3,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": notification_rule_wait.public_primary_key,
                "user_id": user.public_primary_key,
                "type": TYPE_WAIT,
                "duration": timezone.timedelta(seconds=300).seconds,
                "position": notification_rule_wait.order,
                "important": False,
            },
            {
                "id": notification_rule_phone_call.public_primary_key,
                "user_id": user.public_primary_key,
                "type": NotificationChannelPublicAPIOptions.LABELS[notification_rule_phone_call.notify_by],
                "position": notification_rule_phone_call.order,
                "important": False,
            },
            {
                "id": notification_rule_important.public_primary_key,
                "user_id": user.public_primary_key,
                "type": NotificationChannelPublicAPIOptions.LABELS[notification_rule_important.notify_by],
                "position": notification_rule_important.order,
                "important": True,
            },
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_personal_notification_rules_list_important(personal_notification_rule_public_api_setup):
    _, user, token, _, _, notification_rule_important = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    response = client.get(url + "?important=true", format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": notification_rule_important.public_primary_key,
                "user_id": user.public_primary_key,
                "type": NotificationChannelPublicAPIOptions.LABELS[notification_rule_important.notify_by],
                "position": notification_rule_important.order,
                "important": True,
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_personal_notification_rules_list_non_important(personal_notification_rule_public_api_setup):
    (
        _,
        user,
        token,
        notification_rule_wait,
        notification_rule_phone_call,
        _,
    ) = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    response = client.get(url + "?important=false", format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": notification_rule_wait.public_primary_key,
                "user_id": user.public_primary_key,
                "type": TYPE_WAIT,
                "duration": timezone.timedelta(seconds=300).seconds,
                "position": notification_rule_wait.order,
                "important": False,
            },
            {
                "id": notification_rule_phone_call.public_primary_key,
                "user_id": user.public_primary_key,
                "type": NotificationChannelPublicAPIOptions.LABELS[notification_rule_phone_call.notify_by],
                "position": notification_rule_phone_call.order,
                "important": False,
            },
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_update_personal_notification_rule(personal_notification_rule_public_api_setup):
    _, user, token, _, notification_rule_phone_call, _ = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse(
        "api-public:personal_notification_rules-detail", kwargs={"pk": notification_rule_phone_call.public_primary_key}
    )

    data_to_update = {
        "type": NotificationChannelPublicAPIOptions.LABELS[UserNotificationPolicy.NotificationChannel.SMS]
    }
    assert notification_rule_phone_call.notify_by != UserNotificationPolicy.NotificationChannel.SMS
    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)

    expected_response = {
        "id": notification_rule_phone_call.public_primary_key,
        "user_id": user.public_primary_key,
        "type": data_to_update["type"],
        "position": notification_rule_phone_call.order,
        "important": False,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_personal_notification_rule_wait(personal_notification_rule_public_api_setup):
    _, user, token, _, _, _ = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    data_for_create = {
        "user_id": user.public_primary_key,
        "type": TYPE_WAIT,
        "position": 1,
        "duration": timezone.timedelta(seconds=300).seconds,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    expected_response = {
        "id": response.data["id"],
        "user_id": user.public_primary_key,
        "type": TYPE_WAIT,
        "duration": data_for_create["duration"],
        "position": data_for_create["position"],
        "important": False,
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response

    notification_rule = UserNotificationPolicy.objects.get(public_primary_key=response.data["id"])
    assert notification_rule.step == UserNotificationPolicy.Step.WAIT


@pytest.mark.django_db
def test_create_personal_notification_rule_notify_by_sms(personal_notification_rule_public_api_setup):
    _, user, token, _, _, _ = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    data_for_create = {
        "user_id": user.public_primary_key,
        "type": NotificationChannelPublicAPIOptions.LABELS[UserNotificationPolicy.NotificationChannel.SMS],
        "position": 1,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    expected_response = {
        "id": response.data["id"],
        "user_id": user.public_primary_key,
        "type": NotificationChannelPublicAPIOptions.LABELS[UserNotificationPolicy.NotificationChannel.SMS],
        "position": data_for_create["position"],
        "important": False,
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response

    notification_rule = UserNotificationPolicy.objects.get(public_primary_key=response.data["id"])
    assert notification_rule.step == UserNotificationPolicy.Step.NOTIFY
    assert notification_rule.notify_by == UserNotificationPolicy.NotificationChannel.SMS


@pytest.mark.django_db
def test_create_personal_notification_rule_notify_by_sms_important(personal_notification_rule_public_api_setup):
    _, user, token, _, _, _ = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    data_for_create = {
        "user_id": user.public_primary_key,
        "type": NotificationChannelPublicAPIOptions.LABELS[UserNotificationPolicy.NotificationChannel.SMS],
        "position": 1,
        "important": True,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    expected_response = {
        "id": response.data["id"],
        "user_id": user.public_primary_key,
        "type": NotificationChannelPublicAPIOptions.LABELS[UserNotificationPolicy.NotificationChannel.SMS],
        "position": data_for_create["position"],
        "important": data_for_create["important"],
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_personal_notification_rule_invalid_data(personal_notification_rule_public_api_setup):
    _, user, token, _, _, _ = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    data_for_create = {
        "user_id": user.public_primary_key,
        "type": "invalid_type",
        "position": 1,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_delete_personal_notification_rule(personal_notification_rule_public_api_setup):
    _, user, token, notification_rule_wait, _, _ = personal_notification_rule_public_api_setup

    client = APIClient()

    url = reverse(
        "api-public:personal_notification_rules-detail", kwargs={"pk": notification_rule_wait.public_primary_key}
    )

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_204_NO_CONTENT
