import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import NotificationChannelPublicAPIOptions
from apps.public_api import constants as public_api_constants

TYPE_WAIT = "wait"

demo_personal_notification_rule_payload_1 = {
    "id": public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_1,
    "user_id": public_api_constants.DEMO_USER_ID,
    "position": 0,
    "important": False,
    "type": "notify_by_sms",
}

demo_personal_notification_rule_payload_2 = {
    "id": public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_2,
    "user_id": public_api_constants.DEMO_USER_ID,
    "position": 1,
    "duration": timezone.timedelta(seconds=300).seconds,
    "important": False,
    "type": "wait",
}

demo_personal_notification_rule_payload_3 = {
    "id": public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_3,
    "user_id": public_api_constants.DEMO_USER_ID,
    "position": 2,
    "important": False,
    "type": "notify_by_phone_call",
}

demo_personal_notification_rule_payload_4 = {
    "id": public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_4,
    "user_id": public_api_constants.DEMO_USER_ID,
    "position": 0,
    "important": True,
    "type": "notify_by_phone_call",
}

demo_personal_notification_rules_payload = {
    "count": 4,
    "next": None,
    "previous": None,
    "results": [
        demo_personal_notification_rule_payload_1,
        demo_personal_notification_rule_payload_2,
        demo_personal_notification_rule_payload_3,
        demo_personal_notification_rule_payload_4,
    ],
}

demo_personal_notification_rules_non_important_payload = {
    "count": 3,
    "next": None,
    "previous": None,
    "results": [
        demo_personal_notification_rule_payload_1,
        demo_personal_notification_rule_payload_2,
        demo_personal_notification_rule_payload_3,
    ],
}

demo_personal_notification_rules_important_payload = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        demo_personal_notification_rule_payload_4,
    ],
}


@pytest.mark.django_db
def test_get_personal_notification_rule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    _ = make_data_for_demo_token(organization, user)

    demo_personal_notification_rule_1 = UserNotificationPolicy.objects.get(
        public_primary_key=public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_1
    )
    client = APIClient()

    url = reverse(
        "api-public:personal_notification_rules-detail",
        kwargs={"pk": demo_personal_notification_rule_1.public_primary_key},
    )
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_personal_notification_rule_payload_1


@pytest.mark.django_db
def test_get_personal_notification_rules_list(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    _ = make_data_for_demo_token(organization, user)

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_personal_notification_rules_payload


@pytest.mark.django_db
def test_get_personal_notification_rules_list_important(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    _ = make_data_for_demo_token(organization, user)
    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    response = client.get(url + "?important=true", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_personal_notification_rules_important_payload


@pytest.mark.django_db
def test_get_personal_notification_rules_list_non_important(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    _ = make_data_for_demo_token(organization, user)

    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    response = client.get(url + "?important=false", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_personal_notification_rules_non_important_payload


@pytest.mark.django_db
def test_update_personal_notification_rule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    _ = make_data_for_demo_token(organization, user)
    demo_personal_notification_rule_1 = UserNotificationPolicy.objects.get(
        public_primary_key=public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_1
    )
    client = APIClient()

    url = reverse(
        "api-public:personal_notification_rules-detail",
        kwargs={"pk": demo_personal_notification_rule_1.public_primary_key},
    )

    data_to_update = {
        "type": NotificationChannelPublicAPIOptions.LABELS[UserNotificationPolicy.NotificationChannel.SLACK]
    }
    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_personal_notification_rule_payload_1
    # check on nothing change
    demo_personal_notification_rule_1.refresh_from_db()
    assert demo_personal_notification_rule_1.notify_by != UserNotificationPolicy.NotificationChannel.SLACK


@pytest.mark.django_db
def test_create_personal_notification_rule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    _ = make_data_for_demo_token(organization, user)
    client = APIClient()

    url = reverse("api-public:personal_notification_rules-list")
    data_for_create = {
        "user_id": user.public_primary_key,
        "type": TYPE_WAIT,
        "position": 1,
        "duration": timezone.timedelta(seconds=300).seconds,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == demo_personal_notification_rule_payload_1


@pytest.mark.django_db
def test_delete_personal_notification_rule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    _ = make_data_for_demo_token(organization, user)
    demo_personal_notification_rule_1 = UserNotificationPolicy.objects.get(
        public_primary_key=public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_1
    )
    client = APIClient()

    url = reverse(
        "api-public:personal_notification_rules-detail",
        kwargs={"pk": demo_personal_notification_rule_1.public_primary_key},
    )

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    # check on nothing change
    demo_personal_notification_rule_1.refresh_from_db()
    assert demo_personal_notification_rule_1 is not None
