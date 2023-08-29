from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb, ShiftSwapRequest
from common.api_helpers.utils import serialize_datetime_as_utc_timestamp
from common.insight_log import EntityEvent


@pytest.fixture
def setup_swap(make_user_for_organization, make_schedule, make_shift_swap_request):
    def _setup_swap(organization, **kwargs):
        user = make_user_for_organization(organization)
        schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timezone.timedelta(days=1)
        two_days_from_now = tomorrow + timezone.timedelta(days=1)

        swap = make_shift_swap_request(schedule, user, swap_start=tomorrow, swap_end=two_days_from_now)
        return swap

    return _setup_swap


def assert_swap_response(response, request_data):
    response_data = response.json()
    swap = ShiftSwapRequest.objects.get(public_primary_key=response_data["id"])
    # check description
    assert swap.description == response_data["description"]
    if "description" in request_data:
        assert response_data["description"] == request_data["description"]
    # check datetime fields
    for field in ("swap_start", "swap_end"):
        db_value = serialize_datetime_as_utc_timestamp(getattr(swap, field))
        assert db_value == response_data[field]
        if field in request_data:
            assert db_value == request_data[field]
    # check FK fields
    for field in ("schedule", "beneficiary", "benefactor"):
        value = response_data[field]
        if value:
            assert getattr(swap, field).public_primary_key == response_data[field]
        else:
            assert getattr(swap, field) is None
        if field in request_data:
            assert value == request_data[field]


@pytest.mark.django_db
def test_list_filters(
    make_organization_and_user_with_token,
    make_user_for_organization,
    make_schedule,
    make_shift_swap_request,
):
    organization, user, token = make_organization_and_user_with_token()
    user2 = make_user_for_organization(organization)

    schedule1 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    schedule2 = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timezone.timedelta(days=1)
    tomorrow = today + timezone.timedelta(days=1)
    two_days_from_now = tomorrow + timezone.timedelta(days=1)

    # open
    swap1 = make_shift_swap_request(schedule1, user, swap_start=tomorrow, swap_end=two_days_from_now)
    # past due
    swap2 = make_shift_swap_request(schedule1, user2, swap_start=yesterday, swap_end=today)
    # past due / in-progress
    swap3 = make_shift_swap_request(schedule2, user2, swap_start=today, swap_end=tomorrow)
    # taken
    swap4 = make_shift_swap_request(schedule2, user2, swap_start=tomorrow, swap_end=two_days_from_now, benefactor=user)

    def assert_expected(response, expected):
        assert response.status_code == status.HTTP_200_OK
        returned = [s["id"] for s in response.json().get("results", [])]
        assert returned == [s.public_primary_key for s in expected]

    client = APIClient()
    base_url = reverse("api-public:shift_swap-list")

    url = base_url
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert_expected(response, (swap1, swap4))

    url = base_url + f"?schedule_id={schedule1.public_primary_key}"
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert_expected(response, (swap1,))

    url = base_url + "?open_only=true"
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert_expected(response, (swap1,))

    starting_after = serialize_datetime_as_utc_timestamp(yesterday)
    url = base_url + f"?beneficiary={user2.public_primary_key}&starting_after={starting_after}"
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert_expected(response, (swap2, swap3, swap4))

    url = base_url + f"?benefactor={user.public_primary_key}"
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK
    assert_expected(response, (swap4,))


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@patch("apps.api.views.shift_swap.create_shift_swap_request_message")
@pytest.mark.django_db
def test_create(
    mock_create_shift_swap_request_message,
    mock_write_resource_insight_log,
    make_organization_and_user_with_token,
    make_user_for_organization,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()
    another_user = make_user_for_organization(organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timezone.timedelta(days=1)
    two_days_from_now = tomorrow + timezone.timedelta(days=1)

    data = {
        "schedule": schedule.public_primary_key,
        "description": "Taking a few days off",
        "swap_start": serialize_datetime_as_utc_timestamp(tomorrow),
        "swap_end": serialize_datetime_as_utc_timestamp(two_days_from_now),
        "beneficiary": another_user.public_primary_key,
    }

    client = APIClient()
    url = reverse("api-public:shift_swap-list")
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_201_CREATED
    assert_swap_response(response, data)

    ssr = ShiftSwapRequest.objects.get(public_primary_key=response.json()["id"])
    mock_write_resource_insight_log.assert_called_once_with(instance=ssr, author=user, event=EntityEvent.CREATED)
    mock_create_shift_swap_request_message.apply_async.assert_called_once_with((ssr.pk,))


@pytest.mark.django_db
def test_create_requires_beneficiary(
    make_organization_and_user_with_token,
    make_schedule,
):
    organization, user, token = make_organization_and_user_with_token()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timezone.timedelta(days=1)
    two_days_from_now = tomorrow + timezone.timedelta(days=1)

    data = {
        "schedule": schedule.public_primary_key,
        "description": "Taking a few days off",
        "swap_start": serialize_datetime_as_utc_timestamp(tomorrow),
        "swap_end": serialize_datetime_as_utc_timestamp(two_days_from_now),
    }

    client = APIClient()
    url = reverse("api-public:shift_swap-list")
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ShiftSwapRequest.objects.count() == 0


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@patch("apps.api.views.shift_swap.update_shift_swap_request_message")
@pytest.mark.django_db
def test_update(
    mock_update_shift_swap_request_message,
    mock_write_resource_insight_log,
    make_organization_and_user_with_token,
    setup_swap,
):
    organization, user, token = make_organization_and_user_with_token()
    swap = setup_swap(organization)
    assert swap.description is None
    insights_log_prev_state = swap.insight_logs_serialized

    data = {
        "description": "Taking a few days off",
        "schedule": swap.schedule.public_primary_key,
        "swap_start": serialize_datetime_as_utc_timestamp(swap.swap_start),
        "swap_end": serialize_datetime_as_utc_timestamp(swap.swap_end),
    }

    client = APIClient()
    url = reverse("api-public:shift_swap-detail", kwargs={"pk": swap.public_primary_key})
    response = client.put(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert_swap_response(response, data)

    swap.refresh_from_db()
    mock_write_resource_insight_log.assert_called_once_with(
        instance=swap,
        author=user,
        event=EntityEvent.UPDATED,
        prev_state=insights_log_prev_state,
        new_state=swap.insight_logs_serialized,
    )
    mock_update_shift_swap_request_message.apply_async.assert_called_once_with((swap.pk,))


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@patch("apps.api.views.shift_swap.update_shift_swap_request_message")
@pytest.mark.django_db
def test_partial_update(
    mock_update_shift_swap_request_message,
    mock_write_resource_insight_log,
    make_organization_and_user_with_token,
    setup_swap,
):
    organization, user, token = make_organization_and_user_with_token()
    swap = setup_swap(organization)
    assert swap.description is None
    insights_log_prev_state = swap.insight_logs_serialized

    data = {"description": "Taking a few days off"}

    client = APIClient()
    url = reverse("api-public:shift_swap-detail", kwargs={"pk": swap.public_primary_key})
    response = client.patch(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert_swap_response(response, data)

    swap.refresh_from_db()
    mock_write_resource_insight_log.assert_called_once_with(
        instance=swap,
        author=user,
        event=EntityEvent.UPDATED,
        prev_state=insights_log_prev_state,
        new_state=swap.insight_logs_serialized,
    )
    mock_update_shift_swap_request_message.apply_async.assert_called_once_with((swap.pk,))


@pytest.mark.django_db
def test_details(
    make_organization_and_user_with_token,
    make_on_call_shift,
    setup_swap,
):
    organization, _, token = make_organization_and_user_with_token()
    swap = setup_swap(organization)
    schedule = swap.schedule
    user = swap.beneficiary

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(days=1)
    duration = timezone.timedelta(hours=8)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    client = APIClient()
    url = reverse("api-public:shift_swap-detail", kwargs={"pk": swap.public_primary_key})
    response = client.get(url, HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert_swap_response(response, {})

    # include involved shifts information
    shifts_data = response.json()["shifts"]
    assert len(shifts_data) == 1
    expected = [
        # start, end, user, swap request ID
        (
            start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            (start + duration).strftime("%Y-%m-%dT%H:%M:%SZ"),
            user.public_primary_key,
            swap.public_primary_key,
        ),
    ]
    returned_events = [
        (e["start"], e["end"], e["users"][0]["pk"], e["users"][0]["swap_request"]["pk"]) for e in shifts_data
    ]
    assert returned_events == expected


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@patch("apps.api.views.shift_swap.update_shift_swap_request_message")
@pytest.mark.django_db
def test_delete(
    mock_update_shift_swap_request_message,
    mock_write_resource_insight_log,
    make_organization_and_user_with_token,
    setup_swap,
):
    organization, user, token = make_organization_and_user_with_token()
    swap = setup_swap(organization)

    client = APIClient()
    url = reverse("api-public:shift_swap-detail", kwargs={"pk": swap.public_primary_key})

    response = client.delete(url, HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get(url, HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    mock_write_resource_insight_log.assert_called_once_with(
        instance=swap,
        author=user,
        event=EntityEvent.DELETED,
    )
    mock_update_shift_swap_request_message.apply_async.assert_called_once_with((swap.pk,))


@patch("apps.api.views.shift_swap.update_shift_swap_request_message")
@pytest.mark.django_db
def test_take(
    mock_update_shift_swap_request_message,
    make_organization_and_user_with_token,
    make_user_for_organization,
    setup_swap,
):
    organization, user, token = make_organization_and_user_with_token()
    another_user = make_user_for_organization(organization)
    swap = setup_swap(organization)

    client = APIClient()
    url = reverse("api-public:shift_swap-take", kwargs={"pk": swap.public_primary_key})

    data = {"benefactor": another_user.public_primary_key}
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_200_OK

    assert_swap_response(response, data)
    swap.refresh_from_db()
    assert swap.status == ShiftSwapRequest.Statuses.TAKEN
    assert swap.benefactor == another_user

    mock_update_shift_swap_request_message.apply_async.assert_called_once_with((swap.pk,))


@patch("apps.api.views.shift_swap.update_shift_swap_request_message")
@pytest.mark.django_db
def test_take_requires_benefactor(
    mock_update_shift_swap_request_message,
    make_organization_and_user_with_token,
    setup_swap,
):
    organization, user, token = make_organization_and_user_with_token()
    swap = setup_swap(organization)

    client = APIClient()
    url = reverse("api-public:shift_swap-take", kwargs={"pk": swap.public_primary_key})

    data = {}
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    swap.refresh_from_db()
    assert swap.status == ShiftSwapRequest.Statuses.OPEN
    assert swap.benefactor is None

    mock_update_shift_swap_request_message.apply_async.assert_not_called()


@patch("apps.api.views.shift_swap.update_shift_swap_request_message")
@pytest.mark.django_db
def test_take_errors(
    mock_update_shift_swap_request_message,
    make_organization_and_user_with_token,
    make_user_for_organization,
    setup_swap,
):
    organization, user, token = make_organization_and_user_with_token()
    another_user = make_user_for_organization(organization)
    swap = setup_swap(organization)

    client = APIClient()
    url = reverse("api-public:shift_swap-take", kwargs={"pk": swap.public_primary_key})

    # same user taking the swap
    data = {"benefactor": swap.beneficiary.public_primary_key}
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # already taken
    swap.take(another_user)
    data = {"benefactor": another_user.public_primary_key}
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # deleted
    swap = setup_swap(organization)
    swap.delete()
    data = {"benefactor": another_user.public_primary_key}
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # past due
    swap = setup_swap(organization)
    swap.swap_start = timezone.now() - timezone.timedelta(days=2)
    swap.save()
    data = {"benefactor": another_user.public_primary_key}
    response = client.post(url, data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    mock_update_shift_swap_request_message.apply_async.assert_not_called()
