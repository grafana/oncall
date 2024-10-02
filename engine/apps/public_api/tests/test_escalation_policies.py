import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import EscalationPolicy
from apps.public_api.serializers import EscalationPolicySerializer


@pytest.fixture
def escalation_policies_setup():
    def _escalation_policies_setup(organization, user):
        escalation_chain = organization.escalation_chains.create(name="test_chain")

        escalation_policy_notify_persons = escalation_chain.escalation_policies.create(
            step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS
        )
        escalation_policy_notify_persons.notify_to_users_queue.add(user)

        escalation_policy_wait = escalation_chain.escalation_policies.create(
            step=EscalationPolicy.STEP_WAIT,
            wait_delay=EscalationPolicy.FIVE_MINUTES,
        )

        escalation_policy_notify_persons_empty = escalation_chain.escalation_policies.create(
            step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
        )

        escalation_policy_notify_persons_payload = {
            "id": escalation_policy_notify_persons.public_primary_key,
            "escalation_chain_id": escalation_policy_notify_persons.escalation_chain.public_primary_key,
            "position": escalation_policy_notify_persons.order,
            "type": "notify_persons",
            "important": False,
            "persons_to_notify": [user.public_primary_key],
        }

        escalation_policy_wait_payload = {
            "id": escalation_policy_wait.public_primary_key,
            "escalation_chain_id": escalation_policy_wait.escalation_chain.public_primary_key,
            "position": escalation_policy_wait.order,
            "type": "wait",
            "duration": timezone.timedelta(seconds=300).seconds,
        }

        escalation_policy_notify_persons_empty_payload = {
            "id": escalation_policy_notify_persons_empty.public_primary_key,
            "escalation_chain_id": escalation_policy_notify_persons_empty.escalation_chain.public_primary_key,
            "position": escalation_policy_notify_persons_empty.order,
            "type": "notify_persons",
            "important": False,
            "persons_to_notify": [],
        }

        escalation_policies_payload = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                escalation_policy_notify_persons_payload,
                escalation_policy_wait_payload,
                escalation_policy_notify_persons_empty_payload,
            ],
            "current_page_number": 1,
            "page_size": 50,
            "total_pages": 1,
        }
        return (
            escalation_chain,
            (escalation_policy_notify_persons, escalation_policy_wait, escalation_policy_notify_persons_empty),
            escalation_policies_payload,
        )

    return _escalation_policies_setup


@pytest.mark.django_db
def test_get_escalation_policies(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    _, _, escalation_policies_payload = escalation_policies_setup(organization, user)

    client = APIClient()

    url = reverse("api-public:escalation_policies-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    escalation_policies = EscalationPolicy.objects.all()
    serializer = EscalationPolicySerializer(escalation_policies, many=True)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == escalation_policies_payload
    assert response.data["results"] == serializer.data


@pytest.mark.django_db
def test_get_escalation_policies_filter_by_route(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, _, escalation_policies_payload = escalation_policies_setup(organization, user)

    client = APIClient()

    url = reverse("api-public:escalation_policies-list")
    response = client.get(
        url + f"?escalation_chain_id={escalation_chain.public_primary_key}", format="json", HTTP_AUTHORIZATION=token
    )

    escalation_policies = EscalationPolicy.objects.filter(
        escalation_chain__public_primary_key=escalation_chain.public_primary_key
    )

    serializer = EscalationPolicySerializer(escalation_policies, many=True)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == escalation_policies_payload
    assert response.data["results"] == serializer.data


@pytest.mark.django_db
def test_create_escalation_policy(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, _, _ = escalation_policies_setup(organization, user)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": "notify_person_next_each_time",
        "position": 0,
        "persons_to_notify_next_each_time": [user.public_primary_key],
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])
    serializer = EscalationPolicySerializer(escalation_policy)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == serializer.data


@pytest.mark.django_db
def test_create_empty_escalation_policy(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, _, _ = escalation_policies_setup(organization, user)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": None,
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["type"][0] == "This field may not be null."


@pytest.mark.django_db
def test_create_escalation_policy_manual_order_duplicated_position(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, escalation_policies, _ = escalation_policies_setup(organization, user)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": "notify_person_next_each_time",
        "position": 0,
        "persons_to_notify_next_each_time": [user.public_primary_key],
        "manual_order": True,
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["position"] == 0

    for escalation_policy in escalation_policies:
        escalation_policy.refresh_from_db()

    orders = [escalation_policy.order for escalation_policy in escalation_policies]
    assert orders == [3, 1, 2]  # Check orders are swapped when manual_order is True


@pytest.mark.django_db
def test_create_escalation_policy_no_manual_order_duplicated_position(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, escalation_policies, _ = escalation_policies_setup(organization, user)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": "notify_person_next_each_time",
        "position": 0,
        "persons_to_notify_next_each_time": [user.public_primary_key],
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["position"] == 0

    for escalation_policy in escalation_policies:
        escalation_policy.refresh_from_db()

    orders = [escalation_policy.order for escalation_policy in escalation_policies]
    assert orders == [1, 2, 3]  # Check policies are moved down manual_order is False


@pytest.mark.django_db
def test_invalid_step_type(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, _, _ = escalation_policies_setup(organization, user)

    data_for_create = {
        "route_id": escalation_chain.public_primary_key,
        "type": "this_is_invalid_step_type",  # invalid step type
        "position": 0,
        "persons_to_notify_next_each_time": [user.public_primary_key],
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_change_step_importance(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    _, escalation_policies, _ = escalation_policies_setup(organization, user)
    escalation_policy_notify_persons = escalation_policies[0]

    client = APIClient()
    url = reverse(
        "api-public:escalation_policies-detail", kwargs={"pk": escalation_policy_notify_persons.public_primary_key}
    )
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    step_type = escalation_policy_notify_persons.step
    assert step_type not in EscalationPolicy.IMPORTANT_STEPS_SET
    assert response.data["important"] is False

    data_to_change = {"important": True}
    response = client.put(url, data=data_to_change, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["important"] is True
    escalation_policy_notify_persons.refresh_from_db()

    assert escalation_policy_notify_persons.step == EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING[step_type]


@pytest.mark.django_db
def test_create_important_step(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, _, _ = escalation_policies_setup(organization, user)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": "notify_on_call_from_schedule",
        "important": True,
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])

    assert response.status_code == status.HTTP_201_CREATED
    assert escalation_policy.step == EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT
    assert response.data["important"] is True


@pytest.mark.django_db
def test_update_escalation_policy_manual_order_duplicated_position(
    make_organization_and_user_with_token,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    _, escalation_policies, _ = escalation_policies_setup(organization, user)
    escalation_policy_wait = escalation_policies[1]

    client = APIClient()
    url = reverse("api-public:escalation_policies-detail", kwargs={"pk": escalation_policy_wait.public_primary_key})
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.data["position"] != 0

    data_to_change = {"position": 0, "manual_order": True}
    response = client.put(url, data=data_to_change, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK

    for escalation_policy in escalation_policies:
        escalation_policy.refresh_from_db()

    orders = [escalation_policy.order for escalation_policy in escalation_policies]
    assert orders == [1, 0, 2]  # Check orders are swapped when manual_order is True


@pytest.mark.django_db
def test_create_escalation_policy_using_webhooks(
    make_organization_and_user_with_token,
    make_custom_webhook,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    webhook = make_custom_webhook(organization)
    escalation_chain, _, _ = escalation_policies_setup(organization, user)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": "trigger_webhook",
        "position": 0,
        "action_to_trigger": webhook.public_primary_key,
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED

    escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])
    serializer = EscalationPolicySerializer(escalation_policy)
    assert response.data == serializer.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value,expected_status",
    [
        (5, status.HTTP_400_BAD_REQUEST),
        ("5", status.HTTP_400_BAD_REQUEST),
        ("5:00", status.HTTP_400_BAD_REQUEST),
        ("05:00:00", status.HTTP_400_BAD_REQUEST),
        ("05:00:00Z", status.HTTP_200_OK),
    ],
)
def test_update_escalation_policy_from_and_to_time(
    make_organization_and_user_with_token,
    make_escalation_chain,
    make_escalation_policy,
    value,
    expected_status,
):
    organization, _, token = make_organization_and_user_with_token()
    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(escalation_chain, EscalationPolicy.STEP_NOTIFY_IF_TIME)

    client = APIClient()
    url = reverse("api-public:escalation_policies-detail", kwargs={"pk": escalation_policy.public_primary_key})

    for field in ["notify_if_time_from", "notify_if_time_to"]:
        response = client.put(url, data={field: value}, format="json", HTTP_AUTHORIZATION=token)

        assert response.status_code == expected_status

        if expected_status == status.HTTP_200_OK:
            escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])
            serializer = EscalationPolicySerializer(escalation_policy)
            assert response.data == serializer.data
        else:
            assert response.json()[field][0] == "Time has wrong format. Use one of these formats instead: hh:mm:ssZ."


@pytest.mark.django_db
def test_create_escalation_policy_using_notify_team_members(
    make_organization_and_user_with_token,
    make_team,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, _, _ = escalation_policies_setup(organization, user)
    team = make_team(organization)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": "notify_team_members",
        "position": 0,
        "notify_to_team_members": team.team_id,
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED

    escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])
    serializer = EscalationPolicySerializer(escalation_policy)
    assert response.data == serializer.data

    # update to important
    data_to_change = {"important": True}
    url = reverse("api-public:escalation_policies-detail", kwargs={"pk": escalation_policy.public_primary_key})
    response = client.put(url, data=data_to_change, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    escalation_policy.refresh_from_db()
    serializer = EscalationPolicySerializer(escalation_policy)
    assert response.data == serializer.data
    # step is migrated
    assert escalation_policy.step == EscalationPolicy.STEP_NOTIFY_TEAM_MEMBERS_IMPORTANT


@pytest.mark.django_db
def test_update_escalation_policy_using_notify_team_members(
    make_organization_and_user_with_token,
    make_team,
    escalation_policies_setup,
):
    organization, user, token = make_organization_and_user_with_token()
    escalation_chain, _, _ = escalation_policies_setup(organization, user)
    team = make_team(organization)

    data_for_create = {
        "escalation_chain_id": escalation_chain.public_primary_key,
        "type": "notify_team_members",
        "position": 0,
        "notify_to_team_members": team.team_id,
    }

    client = APIClient()
    url = reverse("api-public:escalation_policies-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED

    escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])
    serializer = EscalationPolicySerializer(escalation_policy)
    assert response.data == serializer.data
