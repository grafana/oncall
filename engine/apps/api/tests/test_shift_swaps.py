import datetime
import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.models import OnCallScheduleWeb, ShiftSwapRequest
from common.insight_log import EntityEvent

description = "my shift swap request"
tomorrow = timezone.now() + datetime.timedelta(days=1)
two_days_from_now = tomorrow + datetime.timedelta(days=1)

mock_success_response = Response(status=status.HTTP_200_OK)


@pytest.fixture
def ssr_setup(
    make_schedule, make_organization_and_user_with_plugin_token, make_user_for_organization, make_shift_swap_request
):
    def _ssr_setup(beneficiary_role=None, benefactor_role=None, **kwargs):
        organization, beneficiary, token = make_organization_and_user_with_plugin_token(role=beneficiary_role)
        benefactor = make_user_for_organization(organization, role=benefactor_role)

        schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
        ssr = make_shift_swap_request(schedule, beneficiary, swap_start=tomorrow, swap_end=two_days_from_now, **kwargs)

        return ssr, beneficiary, token, benefactor

    return _ssr_setup


def _convert_dt_to_sr(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _construct_serialized_object(ssr: ShiftSwapRequest, status="open", description=None, benefactor=None):
    return {
        "id": ssr.public_primary_key,
        "created_at": _convert_dt_to_sr(ssr.created_at),
        "updated_at": _convert_dt_to_sr(ssr.updated_at),
        "schedule": ssr.schedule.public_primary_key,
        "swap_start": _convert_dt_to_sr(ssr.swap_start),
        "swap_end": _convert_dt_to_sr(ssr.swap_end),
        "beneficiary": ssr.beneficiary.public_primary_key,
        "status": status,
        "benefactor": benefactor,
        "description": description,
    }


def _build_expected_update_response(ssr, modified_data, updated_at_ts, **kwargs):
    """
    updated_at timestamp will obviously be bumped when we do a PUT/PATCH
    """
    return _construct_serialized_object(ssr, **kwargs) | modified_data | {"updated_at": updated_at_ts}


@pytest.mark.django_db
def test_list(ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, _ = ssr_setup(description=description)
    client = APIClient()
    url = reverse("api-internal:shift_swap-list")

    expected_payload = {
        "next": None,
        "previous": None,
        "page_size": 50,
        "count": 1,
        "current_page_number": 1,
        "total_pages": 1,
        "results": [
            _construct_serialized_object(ssr, description=description),
        ],
    }

    response = client.get(url, format="json", **make_user_auth_headers(beneficiary, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@patch("apps.api.views.shift_swap.ShiftSwapViewSet.list", return_value=mock_success_response)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_list_permissions(
    mock_endpoint_handler,
    ssr_setup,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, beneficiary, token, _ = ssr_setup(beneficiary_role=role)
    client = APIClient()
    url = reverse("api-internal:shift_swap-list")

    response = client.get(url, format="json", **make_user_auth_headers(beneficiary, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_retrieve(ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, _ = ssr_setup(description=description)
    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(beneficiary, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _construct_serialized_object(ssr, description=description)


@patch("apps.api.views.shift_swap.ShiftSwapViewSet.retrieve", return_value=mock_success_response)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_retrieve_permissions(
    mock_endpoint_handler,
    ssr_setup,
    make_user_auth_headers,
    role,
    expected_status,
):
    ssr, _, token, benefactor = ssr_setup(benefactor_role=role)
    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == expected_status


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@pytest.mark.django_db
def test_create(
    mock_write_resource_insight_log, make_organization_and_user_with_plugin_token, make_schedule, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    client = APIClient()
    url = reverse("api-internal:shift_swap-list")

    data = {
        "schedule": schedule.public_primary_key,
        "description": "hellooooo world",
        "swap_start": tomorrow,
        "swap_end": two_days_from_now,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    ssr = ShiftSwapRequest.objects.get(public_primary_key=response.json()["id"])
    expected_response = _construct_serialized_object(ssr) | {
        **data,
        "swap_start": _convert_dt_to_sr(tomorrow),
        "swap_end": _convert_dt_to_sr(two_days_from_now),
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response

    mock_write_resource_insight_log.assert_called_once_with(instance=ssr, author=user, event=EntityEvent.CREATED)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "swap_start,expected_persisted_value",
    [
        # UTC format
        ("2285-07-20T12:00:00Z", "2285-07-20T12:00:00.000000Z"),
        # UTC format w/ microseconds
        ("2285-07-20T12:00:00.245652Z", "2285-07-20T12:00:00.245652Z"),
        # UTC offset w/ colons + no microseconds
        ("2285-07-20T12:00:00+07:00", "2285-07-20T05:00:00.000000Z"),
        # UTC offset w/ colons + microseconds
        ("2285-07-20T12:00:00.245652+07:00", "2285-07-20T05:00:00.245652Z"),
        # UTC offset w/ no colons + no microseconds
        ("2285-07-20T12:00:00+0700", "2285-07-20T05:00:00.000000Z"),
        # UTC offset w/ no colons + microseconds
        ("2285-07-20T12:00:00.245652+0700", "2285-07-20T05:00:00.245652Z"),
        ("2285-07-20 12:00:00", None),
        ("22850720T120000Z", None),
    ],
)
def test_create_swap_start_and_swap_end_must_include_time_zone(
    make_organization_and_user_with_plugin_token,
    make_schedule,
    make_user_auth_headers,
    swap_start,
    expected_persisted_value,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    client = APIClient()
    url = reverse("api-internal:shift_swap-list")

    start_year = "2285"
    end_year = "2286"
    swap_end = swap_start.replace(start_year, end_year)

    data = {
        "schedule": schedule.public_primary_key,
        "description": "hellooooo world",
        "swap_start": swap_start,
        "swap_end": swap_end,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))

    if expected_persisted_value:
        ssr = ShiftSwapRequest.objects.get(public_primary_key=response.json()["id"])

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == _construct_serialized_object(ssr) | {
            **data,
            "swap_start": expected_persisted_value,
            "swap_end": expected_persisted_value.replace(start_year, end_year),
        }
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("apps.api.views.shift_swap.ShiftSwapViewSet.create", return_value=mock_success_response)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_create_permissions(
    mock_endpoint_handler,
    ssr_setup,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, _, token, benefactor = ssr_setup(benefactor_role=role)
    client = APIClient()
    url = reverse("api-internal:shift_swap-list")

    response = client.post(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == expected_status


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@pytest.mark.django_db
def test_update(mock_write_resource_insight_log, ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, _ = ssr_setup(description=description)
    insights_log_prev_state = ssr.insight_logs_serialized

    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})
    auth_headers = make_user_auth_headers(beneficiary, token)

    data = {
        "description": "hellooooo world",
        "schedule": ssr.schedule.public_primary_key,
        "swap_start": _convert_dt_to_sr(ssr.swap_start),
        "swap_end": _convert_dt_to_sr(ssr.swap_end),
    }

    response = client.put(url, data=json.dumps(data), content_type="application/json", **auth_headers)
    response_json = response.json()
    expected_response = _build_expected_update_response(ssr, data, response_json["updated_at"], description=description)
    assert response.status_code == status.HTTP_200_OK
    assert response_json == expected_response

    response = client.get(url, format="json", **auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    ssr.refresh_from_db()
    mock_write_resource_insight_log.assert_called_once_with(
        instance=ssr,
        author=beneficiary,
        event=EntityEvent.UPDATED,
        prev_state=insights_log_prev_state,
        new_state=ssr.insight_logs_serialized,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "swap_start,expected_persisted_value",
    [
        # UTC format
        ("2285-07-20T12:00:00Z", "2285-07-20T12:00:00.000000Z"),
        # UTC format w/ microseconds
        ("2285-07-20T12:00:00.245652Z", "2285-07-20T12:00:00.245652Z"),
        # UTC offset w/ colons + no microseconds
        ("2285-07-20T12:00:00+07:00", "2285-07-20T05:00:00.000000Z"),
        # UTC offset w/ colons + microseconds
        ("2285-07-20T12:00:00.245652+07:00", "2285-07-20T05:00:00.245652Z"),
        # UTC offset w/ no colons + no microseconds
        ("2285-07-20T12:00:00+0700", "2285-07-20T05:00:00.000000Z"),
        # UTC offset w/ no colons + microseconds
        ("2285-07-20T12:00:00.245652+0700", "2285-07-20T05:00:00.245652Z"),
        ("2285-07-20 12:00:00", None),
        ("22850720T120000Z", None),
    ],
)
def test_update_swap_start_and_swap_end_must_include_time_zone(
    ssr_setup,
    make_user_auth_headers,
    swap_start,
    expected_persisted_value,
):
    ssr, beneficiary, token, _ = ssr_setup()

    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    start_year = "2285"
    end_year = "2286"
    swap_end = swap_start.replace(start_year, end_year)

    data = {
        "schedule": ssr.schedule.public_primary_key,
        "swap_start": swap_start,
        "swap_end": swap_end,
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(beneficiary, token))

    if expected_persisted_value:
        ssr = ShiftSwapRequest.objects.get(public_primary_key=response.json()["id"])

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == _construct_serialized_object(ssr) | {
            **data,
            "swap_start": expected_persisted_value,
            "swap_end": expected_persisted_value.replace(start_year, end_year),
        }
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_update_own_ssr_permissions(ssr_setup, make_user_auth_headers, role, expected_status):
    ssr, beneficiary, token, _ = ssr_setup(beneficiary_role=role)
    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    data = {
        "description": "hellooooo world",
        "schedule": ssr.schedule.public_primary_key,
        "swap_start": _convert_dt_to_sr(ssr.swap_start),
        "swap_end": _convert_dt_to_sr(ssr.swap_end),
    }

    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(beneficiary, token)
    )
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_update_others_ssr_permissions(ssr_setup, make_user_auth_headers):
    ssr, _, token, benefactor = ssr_setup()
    assert benefactor.role == LegacyAccessControlRole.ADMIN

    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    response = client.put(
        url, data=json.dumps({}), content_type="application/json", **make_user_auth_headers(benefactor, token)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@pytest.mark.django_db
def test_partial_update(mock_write_resource_insight_log, ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, _ = ssr_setup(description=description)
    insights_log_prev_state = ssr.insight_logs_serialized

    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})
    auth_headers = make_user_auth_headers(beneficiary, token)

    data = {"description": "this is a shift swap request"}

    response = client.patch(url, data=json.dumps(data), content_type="application/json", **auth_headers)
    response_json = response.json()
    expected_response = _build_expected_update_response(ssr, data, response_json["updated_at"], description=description)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    response = client.get(url, format="json", **auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    ssr.refresh_from_db()
    mock_write_resource_insight_log.assert_called_once_with(
        instance=ssr,
        author=beneficiary,
        event=EntityEvent.UPDATED,
        prev_state=insights_log_prev_state,
        new_state=ssr.insight_logs_serialized,
    )


@pytest.mark.django_db
def test_partial_update_time_related_fields(ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, _ = ssr_setup()
    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})
    auth_headers = make_user_auth_headers(beneficiary, token)

    # but if we do PATCH a time related field, we must specify all the time fields
    swap_start = {"swap_start": _convert_dt_to_sr(tomorrow + datetime.timedelta(days=5))}
    swap_end = {"swap_end": _convert_dt_to_sr(tomorrow + datetime.timedelta(days=10))}
    valid = swap_start | swap_end

    for case in [swap_start, swap_end]:
        response = client.patch(url, data=json.dumps(case), content_type="application/json", **auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # valid way to patch time related fields
    response = client.patch(url, data=json.dumps(valid), content_type="application/json", **auth_headers)
    response_json = response.json()
    expected_response = _build_expected_update_response(ssr, valid, response_json["updated_at"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    response = client.get(url, format="json", **auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_partial_update_own_ssr_permissions(ssr_setup, make_user_auth_headers, role, expected_status):
    ssr, beneficiary, token, _ = ssr_setup(beneficiary_role=role)
    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    response = client.patch(
        url,
        data=json.dumps({"description": "foo"}),
        content_type="application/json",
        **make_user_auth_headers(beneficiary, token),
    )
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_partial_update_others_ssr_permissions(ssr_setup, make_user_auth_headers):
    ssr, _, token, benefactor = ssr_setup()
    assert benefactor.role == LegacyAccessControlRole.ADMIN

    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    response = client.patch(
        url, data=json.dumps({}), content_type="application/json", **make_user_auth_headers(benefactor, token)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_benefactor_and_beneficiary_are_read_only_fields(ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, benefactor = ssr_setup(description=description)

    client = APIClient()
    list_url = reverse("api-internal:shift_swap-list")
    detail_url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})
    auth_headers = make_user_auth_headers(beneficiary, token)

    base_data = {
        "description": "hellooooo world",
        "schedule": ssr.schedule.public_primary_key,
        "swap_start": _convert_dt_to_sr(ssr.swap_start),
        "swap_end": _convert_dt_to_sr(ssr.swap_end),
    }

    update_beneficiary = {"beneficiary": benefactor.public_primary_key}
    update_benefactor = {"benefactor": beneficiary.public_primary_key}

    def _assert_beneficiary_hasnt_changed(resp):
        assert resp.json()["beneficiary"] == beneficiary.public_primary_key

    def _assert_benefactor_is_still_none(resp):
        assert resp.json()["benefactor"] is None

    response = client.post(
        list_url, data=json.dumps(base_data | update_beneficiary), content_type="application/json", **auth_headers
    )
    _assert_beneficiary_hasnt_changed(response)

    response = client.post(
        list_url, data=json.dumps(base_data | update_benefactor), content_type="application/json", **auth_headers
    )
    _assert_benefactor_is_still_none(response)

    response = client.put(
        detail_url, data=json.dumps(base_data | update_beneficiary), content_type="application/json", **auth_headers
    )
    _assert_beneficiary_hasnt_changed(response)

    response = client.put(
        detail_url, data=json.dumps(base_data | update_benefactor), content_type="application/json", **auth_headers
    )
    _assert_benefactor_is_still_none(response)

    response = client.patch(
        detail_url, data=json.dumps(base_data | update_beneficiary), content_type="application/json", **auth_headers
    )
    _assert_beneficiary_hasnt_changed(response)

    response = client.patch(
        detail_url, data=json.dumps(base_data | update_benefactor), content_type="application/json", **auth_headers
    )
    _assert_benefactor_is_still_none(response)


@patch("apps.api.views.shift_swap.write_resource_insight_log")
@pytest.mark.django_db
def test_delete(mock_write_resource_insight_log, ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, _ = ssr_setup()
    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})
    auth_headers = make_user_auth_headers(beneficiary, token)

    response = client.delete(url, **auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get(url, format="json", **auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    mock_write_resource_insight_log.assert_called_once_with(
        instance=ssr,
        author=beneficiary,
        event=EntityEvent.DELETED,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_delete_own_ssr_permissions(ssr_setup, make_user_auth_headers, role, expected_status):
    ssr, beneficiary, token, _ = ssr_setup(beneficiary_role=role)
    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    response = client.delete(url, format="json", **make_user_auth_headers(beneficiary, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_delete_others_ssr_permissions(ssr_setup, make_user_auth_headers):
    ssr, _, token, benefactor = ssr_setup()
    assert benefactor.role == LegacyAccessControlRole.ADMIN

    client = APIClient()
    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})

    response = client.delete(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_take(ssr_setup, make_user_auth_headers):
    ssr, _, token, benefactor = ssr_setup()
    client = APIClient()
    url = reverse("api-internal:shift_swap-take", kwargs={"pk": ssr.public_primary_key})
    auth_headers = make_user_auth_headers(benefactor, token)

    response = client.post(url, format="json", **auth_headers)
    response_json = response.json()
    updated_at = response_json["updated_at"]
    expected_response = _build_expected_update_response(
        ssr, {}, updated_at, status="taken", benefactor=benefactor.public_primary_key
    )

    assert response.status_code == status.HTTP_200_OK
    assert response_json == expected_response
    assert updated_at != _convert_dt_to_sr(ssr.updated_at)  # validate that updated_at is auto-updated on take

    url = reverse("api-internal:shift_swap-detail", kwargs={"pk": ssr.public_primary_key})
    response = client.get(url, format="json", **auth_headers)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json == expected_response


@pytest.mark.django_db
def test_benficiary_tries_to_take_their_own_ssr(ssr_setup, make_user_auth_headers):
    ssr, beneficiary, token, _ = ssr_setup()
    client = APIClient()
    url = reverse("api-internal:shift_swap-take", kwargs={"pk": ssr.public_primary_key})

    response = client.post(url, format="json", **make_user_auth_headers(beneficiary, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_take_already_taken_ssr(ssr_setup, make_user_auth_headers):
    ssr, _, token, benefactor = ssr_setup()
    client = APIClient()
    url = reverse("api-internal:shift_swap-take", kwargs={"pk": ssr.public_primary_key})

    response = client.post(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == status.HTTP_200_OK

    response = client.post(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_take_past_due_ssr(ssr_setup, make_user_auth_headers):
    ssr, _, token, benefactor = ssr_setup()
    client = APIClient()
    url = reverse("api-internal:shift_swap-take", kwargs={"pk": ssr.public_primary_key})

    ssr.swap_start = tomorrow - datetime.timedelta(days=5)
    ssr.save()

    response = client.post(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_take_deleted_ssr(ssr_setup, make_user_auth_headers):
    ssr, _, token, benefactor = ssr_setup()
    client = APIClient()
    url = reverse("api-internal:shift_swap-take", kwargs={"pk": ssr.public_primary_key})

    ssr.delete()

    response = client.post(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("apps.api.views.shift_swap.ShiftSwapViewSet.take", return_value=mock_success_response)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_take_permissions(
    mock_endpoint_handler,
    ssr_setup,
    make_user_auth_headers,
    role,
    expected_status,
):
    ssr, _, token, benefactor = ssr_setup(benefactor_role=role)
    client = APIClient()
    url = reverse("api-internal:shift_swap-take", kwargs={"pk": ssr.public_primary_key})

    response = client.post(url, format="json", **make_user_auth_headers(benefactor, token))
    assert response.status_code == expected_status
