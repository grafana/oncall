from unittest.mock import patch

import pytest
from django.db.models import Max
from django.urls import reverse
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import EscalationPolicy
from apps.api.permissions import LegacyAccessControlRole


@pytest.fixture()
def escalation_policy_internal_api_setup(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_user_for_organization,
    make_escalation_policy,
):
    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.ONE_MINUTE,
    )
    return token, escalation_chain, escalation_policy, first_user, second_user


@pytest.mark.django_db
def test_create_escalation_policy(escalation_policy_internal_api_setup, make_user_auth_headers):
    token, escalation_chain, _, user, _ = escalation_policy_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:escalation_policy-list")

    data = {
        "step": EscalationPolicy.STEP_WAIT,
        "wait_delay": "60.0",
        "escalation_chain": escalation_chain.public_primary_key,
        "notify_to_users_queue": [],
        "from_time": None,
        "to_time": None,
    }

    max_order = EscalationPolicy.objects.filter(escalation_chain=escalation_chain).aggregate(maxorder=Max("order"))[
        "maxorder"
    ]

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_201_CREATED
    assert EscalationPolicy.objects.get(public_primary_key=response.data["id"]).order == max_order + 1


@pytest.mark.django_db
@pytest.mark.parametrize("wait_delay", (timedelta(seconds=59), timedelta(hours=24, seconds=1)))
def test_create_escalation_policy_wait_delay_invalid(
    escalation_policy_internal_api_setup, make_user_auth_headers, wait_delay
):
    token, escalation_chain, _, user, _ = escalation_policy_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:escalation_policy-list")

    data = {
        "step": EscalationPolicy.STEP_WAIT,
        "wait_delay": str(wait_delay.total_seconds()),
        "escalation_chain": escalation_chain.public_primary_key,
        "notify_to_users_queue": [],
        "from_time": None,
        "to_time": None,
    }

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_escalation_policy_webhook(
    escalation_policy_internal_api_setup, make_custom_webhook, make_user_auth_headers
):
    token, escalation_chain, _, user, _ = escalation_policy_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:escalation_policy-list")

    webhook = make_custom_webhook(organization=user.organization)
    data = {
        "step": EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK,
        "escalation_chain": escalation_chain.public_primary_key,
        "custom_webhook": webhook.public_primary_key,
    }

    max_order = EscalationPolicy.objects.filter(escalation_chain=escalation_chain).aggregate(maxorder=Max("order"))[
        "maxorder"
    ]

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["custom_webhook"] == webhook.public_primary_key
    escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])
    assert escalation_policy.order == max_order + 1
    assert escalation_policy.custom_webhook == webhook


@pytest.mark.django_db
def test_update_notify_multiple_users_step(escalation_policy_internal_api_setup, make_user_auth_headers):
    token, _, escalation_policy, first_user, second_user = escalation_policy_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    data = {
        "step": EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
        "notify_to_users_queue": [first_user.public_primary_key, second_user.public_primary_key],
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(first_user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["step"] == EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS
    assert sorted(response.json()["notify_to_users_queue"]) == sorted(
        [first_user.public_primary_key, second_user.public_primary_key]
    )


@pytest.mark.django_db
def test_manage_escalation_policy_notify_team(escalation_policy_internal_api_setup, make_team, make_user_auth_headers):
    token, escalation_chain, _, user, _ = escalation_policy_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:escalation_policy-list")

    team = make_team(organization=user.organization)
    data = {
        "step": EscalationPolicy.STEP_NOTIFY_TEAM_MEMBERS,
        "escalation_chain": escalation_chain.public_primary_key,
        "notify_to_team_members": team.public_primary_key,
    }

    max_order = EscalationPolicy.objects.filter(escalation_chain=escalation_chain).aggregate(maxorder=Max("order"))[
        "maxorder"
    ]

    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["notify_to_team_members"] == team.public_primary_key
    escalation_policy = EscalationPolicy.objects.get(public_primary_key=response.data["id"])
    assert escalation_policy.order == max_order + 1
    assert escalation_policy.notify_to_team_members == team

    # update team in policy
    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})
    another_team = make_team(organization=user.organization)
    data = {
        "step": EscalationPolicy.STEP_NOTIFY_TEAM_MEMBERS,
        "notify_to_team_members": another_team.public_primary_key,
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["step"] == EscalationPolicy.STEP_NOTIFY_TEAM_MEMBERS
    assert response.json()["notify_to_team_members"] == another_team.public_primary_key


@pytest.mark.django_db
def test_move_to_position(escalation_policy_internal_api_setup, make_user_auth_headers):
    token, _, escalation_policy, user, _ = escalation_policy_internal_api_setup
    client = APIClient()

    position_to_move = 0
    url = reverse(
        "api-internal:escalation_policy-move-to-position", kwargs={"pk": escalation_policy.public_primary_key}
    )
    response = client.put(
        f"{url}?position={position_to_move}", content_type="application/json", **make_user_auth_headers(user, token)
    )
    escalation_policy.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert escalation_policy.order == position_to_move


@pytest.mark.django_db
def test_move_to_position_invalid_index(escalation_policy_internal_api_setup, make_user_auth_headers):
    token, _, escalation_policy, user, _ = escalation_policy_internal_api_setup
    client = APIClient()

    position_to_move = 1
    url = reverse(
        "api-internal:escalation_policy-move-to-position", kwargs={"pk": escalation_policy.public_primary_key}
    )
    response = client.put(
        f"{url}?position={position_to_move}", content_type="application/json", **make_user_auth_headers(user, token)
    )
    escalation_policy.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-list")

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.create",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.update",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(user, token))

        assert response.status_code == expected_status

        response = client.patch(url, format="json", **make_user_auth_headers(user, token))

        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-list")

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.retrieve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.destroy",
        return_value=Response(
            status=status.HTTP_204_NO_CONTENT,
        ),
    ):
        response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_escalation_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-escalation-options")

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.escalation_options",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_delay_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)

    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-delay-options")

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.delay_options",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_escalation_policy_move_to_position_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)

    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, wait_delay=EscalationPolicy.ONE_MINUTE
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    with patch(
        "apps.api.views.escalation_policy.EscalationPolicyView.move_to_position",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "important_step ,expected_default_step",
    [
        (EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT, EscalationPolicy.STEP_NOTIFY_GROUP),
        (EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT, EscalationPolicy.STEP_NOTIFY_SCHEDULE),
        (EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT, EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS),
    ],
)
def test_escalation_policy_maps_default_to_important(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_escalation_chain,
    make_escalation_policy,
    important_step,
    expected_default_step,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain,
        escalation_policy_step=important_step,
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.json()["step"] == expected_default_step
    assert response.json()["important"] is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    "default_step",
    [
        EscalationPolicy.STEP_NOTIFY_GROUP,
        EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    ],
)
def test_escalation_policy_default_steps_stay_default(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_escalation_policy,
    default_step,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain,
        escalation_policy_step=default_step,
    )
    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.json()["step"] == default_step
    assert response.json()["important"] is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "default_step ,expected_important_step",
    [
        (EscalationPolicy.STEP_NOTIFY_GROUP, EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT),
        (EscalationPolicy.STEP_NOTIFY_SCHEDULE, EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT),
        (EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS, EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT),
    ],
)
def test_create_escalation_policy_important(
    make_organization_and_user_with_slack_identities,
    make_token_for_organization,
    make_escalation_chain,
    default_step,
    expected_important_step,
    make_user_auth_headers,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)
    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    data_for_creation = {
        "escalation_chain": escalation_chain.public_primary_key,
        "step": default_step,
        "important": True,
    }
    url = reverse("api-internal:escalation_policy-list")

    response = client.post(url, data=data_for_creation, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_201_CREATED
    public_primary_key = response.json()["id"]
    created_escalation_policy = EscalationPolicy.objects.get(public_primary_key=public_primary_key)
    assert created_escalation_policy.step == expected_important_step


@pytest.mark.django_db
@pytest.mark.parametrize(
    "default_step",
    [
        EscalationPolicy.STEP_NOTIFY_GROUP,
        EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    ],
)
def test_create_escalation_policy_default(
    make_organization_and_user_with_slack_identities,
    make_token_for_organization,
    make_escalation_chain,
    default_step,
    make_user_auth_headers,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)
    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    data_for_creation = {
        "escalation_chain": escalation_chain.public_primary_key,
        "step": default_step,
        "important": False,
    }
    url = reverse("api-internal:escalation_policy-list")

    response = client.post(url, data=data_for_creation, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_201_CREATED
    public_primary_key = response.json()["id"]
    created_escalation_policy = EscalationPolicy.objects.get(public_primary_key=public_primary_key)
    assert created_escalation_policy.step == default_step


@pytest.mark.django_db
@pytest.mark.parametrize("step", EscalationPolicy.STEPS_WITH_NO_IMPORTANT_VERSION_SET)
def test_create_escalation_policy_with_no_important_version(
    make_organization_and_user_with_slack_identities,
    make_token_for_organization,
    make_escalation_chain,
    step,
    make_user_auth_headers,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)
    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    data_for_creation = {
        "escalation_chain": escalation_chain.public_primary_key,
        "step": step,
    }
    url = reverse("api-internal:escalation_policy-list")

    response = client.post(url, data=data_for_creation, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_201_CREATED
    public_primary_key = response.json()["id"]
    created_escalation_policy = EscalationPolicy.objects.get(public_primary_key=public_primary_key)
    assert created_escalation_policy.step == step


@pytest.mark.django_db
@pytest.mark.parametrize("step", EscalationPolicy.STEPS_WITH_NO_IMPORTANT_VERSION_SET)
def test_escalation_policy_can_not_create_invalid_important_step(
    make_organization_and_user_with_slack_identities,
    make_token_for_organization,
    make_escalation_chain,
    step,
    make_user_auth_headers,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)
    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    data_for_creation = {"escalation_chain": escalation_chain.public_primary_key, "step": step, "important": True}
    url = reverse("api-internal:escalation_policy-list")

    response = client.post(url, data=data_for_creation, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize("step", EscalationPolicy.INTERNAL_API_STEPS)
def test_escalation_policy_can_not_create_with_non_step_type_related_data(
    make_organization_and_user_with_slack_identities,
    make_token_for_organization,
    make_escalation_chain,
    step,
    make_user_auth_headers,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)

    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    data_for_creation = {
        "escalation_chain": escalation_chain.public_primary_key,
        "step": step,
        "notify_to_users_queue": [user.public_primary_key],
        "wait_delay": "300.0",
        "from_time": "06:50:00",
        "to_time": "04:10:00",
    }
    url = reverse("api-internal:escalation_policy-list")

    response = client.post(url, data=data_for_creation, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize(
    "step, related_fields",
    [
        (EscalationPolicy.STEP_WAIT, ["wait_delay"]),
        (EscalationPolicy.STEP_FINAL_NOTIFYALL, []),
        (EscalationPolicy.STEP_FINAL_RESOLVE, []),
        (EscalationPolicy.STEP_NOTIFY_GROUP, ["notify_to_group"]),
        (EscalationPolicy.STEP_NOTIFY_SCHEDULE, ["notify_schedule"]),
        (EscalationPolicy.STEP_NOTIFY_USERS_QUEUE, ["notify_to_users_queue"]),
        (EscalationPolicy.STEP_NOTIFY_IF_TIME, ["from_time", "to_time"]),
        (EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS, ["notify_to_users_queue"]),
        (EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK, ["custom_webhook"]),
    ],
)
def test_escalation_policy_update_drop_non_step_type_related_data(
    make_organization_and_user_with_slack_identities,
    make_token_for_organization,
    make_escalation_chain,
    make_escalation_policy,
    step,
    related_fields,
    make_user_auth_headers,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)

    escalation_chain = make_escalation_chain(organization)

    data_for_creation = {
        "wait_delay": timedelta(minutes=5),
        "from_time": "06:50:00",
        "to_time": "04:10:00",
    }

    escalation_policy = make_escalation_policy(
        escalation_chain=escalation_chain, escalation_policy_step=EscalationPolicy.STEP_WAIT, **data_for_creation
    )

    escalation_policy.notify_to_users_queue.set([user])

    data_for_update = {"step": step}

    fields_to_check = [
        "wait_delay",
        "notify_schedule",
        "notify_to_users_queue",
        "notify_to_group",
        "notify_to_team_members",
        "from_time",
        "to_time",
        "custom_webhook",
    ]
    for f in related_fields:
        fields_to_check.remove(f)

    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    response = client.put(url, data=data_for_update, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK

    escalation_policy.refresh_from_db()

    for f in fields_to_check:
        if f == "notify_to_users_queue":
            assert len(list(getattr(escalation_policy, f).all())) == 0
        else:
            assert getattr(escalation_policy, f) is None


@pytest.mark.django_db
@pytest.mark.parametrize("step", EscalationPolicy.DEFAULT_STEPS_SET)
def test_escalation_policy_switch_importance(
    make_organization_and_user_with_slack_identities,
    make_token_for_organization,
    make_escalation_chain,
    make_escalation_policy,
    step,
    make_user_auth_headers,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    _, token = make_token_for_organization(organization)
    escalation_chain = make_escalation_chain(organization)

    escalation_policy = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=step,
    )
    data_for_update = {
        "id": escalation_policy.public_primary_key,
        "step": escalation_policy.step,
        "escalation_chain": escalation_chain.public_primary_key,
        "notify_to_users_queue": [],
        "from_time": None,
        "to_time": None,
        "num_alerts_in_window": None,
        "num_minutes_in_window": None,
        "slack_integration_required": escalation_policy.slack_integration_required,
        "custom_webhook": None,
        "notify_schedule": None,
        "notify_to_group": None,
        "notify_to_team_members": None,
        "important": True,
        "wait_delay": None,
    }

    client = APIClient()

    url = reverse("api-internal:escalation_policy-detail", kwargs={"pk": escalation_policy.public_primary_key})

    response = client.put(url, data=data_for_update, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == data_for_update


@pytest.mark.django_db
def test_escalation_policy_filter_by_user(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_escalation_chain,
    make_escalation_policy,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)
    escalation_chain = make_escalation_chain(organization)

    client = APIClient()
    escalation_policy_with_one_user = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )

    escalation_policy_with_two_users = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )

    escalation_policy_with_one_user.notify_to_users_queue.set([user])
    escalation_policy_with_two_users.notify_to_users_queue.set([user, second_user])

    expected_payload = [
        {
            "id": escalation_policy_with_one_user.public_primary_key,
            "step": 13,
            "wait_delay": None,
            "escalation_chain": escalation_chain.public_primary_key,
            "notify_to_users_queue": [user.public_primary_key],
            "from_time": None,
            "to_time": None,
            "num_alerts_in_window": None,
            "num_minutes_in_window": None,
            "slack_integration_required": False,
            "custom_webhook": None,
            "notify_schedule": None,
            "notify_to_group": None,
            "notify_to_team_members": None,
            "important": False,
        },
        {
            "id": escalation_policy_with_two_users.public_primary_key,
            "step": 13,
            "wait_delay": None,
            "escalation_chain": escalation_chain.public_primary_key,
            "notify_to_users_queue": [user.public_primary_key, second_user.public_primary_key],
            "from_time": None,
            "to_time": None,
            "num_alerts_in_window": None,
            "num_minutes_in_window": None,
            "slack_integration_required": False,
            "custom_webhook": None,
            "notify_schedule": None,
            "notify_to_group": None,
            "notify_to_team_members": None,
            "important": False,
        },
    ]

    url = reverse("api-internal:escalation_policy-list")

    response = client.get(f"{url}?user={user.public_primary_key}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK

    result = response.json()
    assert set(result[1]["notify_to_users_queue"]) == {user.public_primary_key, second_user.public_primary_key}
    expected_payload[1]["notify_to_users_queue"] = result[1]["notify_to_users_queue"]
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_escalation_policy_filter_by_slack_channel(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_slack_channel,
    make_escalation_policy,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    slack_channel = make_slack_channel(organization.slack_team_identity)
    escalation_chain = make_escalation_chain(organization)
    other_escalation_chain = make_escalation_chain(organization)
    make_channel_filter(
        alert_receive_channel,
        escalation_chain=escalation_chain,
        is_default=False,
        slack_channel_id=slack_channel.slack_id,
    )

    client = APIClient()

    make_escalation_policy(
        escalation_chain=other_escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
    )

    escalation_policy_from_alert_receive_channel_with_slack_channel = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
    )
    expected_payload = [
        {
            "id": escalation_policy_from_alert_receive_channel_with_slack_channel.public_primary_key,
            "step": 0,
            "wait_delay": None,
            "escalation_chain": escalation_chain.public_primary_key,
            "notify_to_users_queue": [],
            "from_time": None,
            "to_time": None,
            "num_alerts_in_window": None,
            "num_minutes_in_window": None,
            "slack_integration_required": False,
            "custom_webhook": None,
            "notify_schedule": None,
            "notify_to_group": None,
            "notify_to_team_members": None,
            "important": False,
        },
    ]

    url = reverse("api-internal:escalation_policy-list")

    response = client.get(
        f"{url}?slack_channel={slack_channel.slack_id}", format="json", **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == expected_payload


@pytest.mark.django_db
def test_escalation_policy_escalation_options_webhooks(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse("api-internal:escalation_policy-escalation-options")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    returned_options = [option["value"] for option in response.json()]

    assert EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK in returned_options
