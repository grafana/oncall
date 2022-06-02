import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import EscalationPolicy
from apps.public_api import constants as public_api_constants

# https://api-docs.amixr.io/#get-escalation-policy
demo_escalation_policy_payload = {
    "id": public_api_constants.DEMO_ESCALATION_POLICY_ID_1,
    "escalation_chain_id": public_api_constants.DEMO_ESCALATION_CHAIN_ID,
    "position": 0,
    "type": "wait",
    "duration": timezone.timedelta(seconds=60).seconds,
}

# https://api-docs.amixr.io/#list-escalation-policies
demo_escalation_policies_payload = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": public_api_constants.DEMO_ESCALATION_POLICY_ID_1,
            "escalation_chain_id": public_api_constants.DEMO_ESCALATION_CHAIN_ID,
            "position": 0,
            "type": "wait",
            "duration": timezone.timedelta(seconds=60).seconds,
        },
        {
            "id": public_api_constants.DEMO_ESCALATION_POLICY_ID_2,
            "escalation_chain_id": public_api_constants.DEMO_ESCALATION_CHAIN_ID,
            "position": 1,
            "type": "notify_person_next_each_time",
            "persons_to_notify_next_each_time": ["U4DNY931HHJS5"],
        },
    ],
}


@pytest.mark.django_db
def test_get_escalation_policies(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:escalation_policies-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_escalation_policies_payload


@pytest.mark.django_db
def test_get_escalation_policies_filter_by_route(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:escalation_policies-list")
    response = client.get(
        url + f"?route_id={public_api_constants.DEMO_ROUTE_ID_1}", format="json", HTTP_AUTHORIZATION=token
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_escalation_policies_payload


@pytest.mark.django_db
def test_create_escalation_policy(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    data_for_create = {
        "escalation_chain_id": public_api_constants.DEMO_ESCALATION_CHAIN_ID,
        "type": "notify_person_next_each_time",
        "position": 0,
        "persons_to_notify_next_each_time": [user.public_primary_key],
    }
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED
    # check on nothing change
    assert response.json() == demo_escalation_policy_payload


@pytest.mark.django_db
def test_invalid_step_type(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    data_for_create = {
        "escalation_chain_id": public_api_constants.DEMO_ESCALATION_CHAIN_ID,
        "type": "this_is_invalid_step_type",  # invalid step type
        "position": 0,
        "persons_to_notify_next_each_time": [user.public_primary_key],
    }
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED
    # check on nothing change
    assert response.json() == demo_escalation_policy_payload


@pytest.mark.django_db
def test_update_escalation_step(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    data_for_update = {
        "route_id": public_api_constants.DEMO_ROUTE_ID_1,
        "type": "notify_person_next_each_time",
        "position": 1,
        "persons_to_notify_next_each_time": [user.public_primary_key],
    }
    url = reverse(
        "api-public:escalation_policies-detail", kwargs={"pk": public_api_constants.DEMO_ESCALATION_POLICY_ID_1}
    )
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    # check on nothing change
    assert response.json() == demo_escalation_policy_payload


@pytest.mark.django_db
def test_delete_escalation_policy(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    escalation_policy = EscalationPolicy.objects.get(
        public_primary_key=public_api_constants.DEMO_ESCALATION_POLICY_ID_1
    )

    url = reverse("api-public:escalation_policies-detail", args=[escalation_policy.public_primary_key])
    response = client.delete(url, format="json", HTTP_AUTHORIZATION=token)

    escalation_policy.refresh_from_db()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    # check on nothing change
    escalation_policy.refresh_from_db()
    assert escalation_policy is not None
