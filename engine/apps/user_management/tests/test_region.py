from unittest.mock import patch

import pytest
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.auth_token.auth import ApiTokenAuthentication, ScheduleExportAuthentication, UserScheduleExportAuthentication
from apps.auth_token.models import ScheduleExportAuthToken, UserScheduleExportAuthToken
from apps.integrations.views import AlertManagerAPIView
from apps.schedules.models import OnCallScheduleWeb
from apps.user_management.exceptions import OrganizationMovedException


@pytest.mark.django_db
def test_organization_region_delete(
    make_organization_and_region,
):
    organization, region = make_organization_and_region()
    organization.save()

    organization.refresh_from_db()
    assert organization.migration_destination.slug == region.slug
    region.delete()

    organization.refresh_from_db()
    assert organization.migration_destination is None


@pytest.mark.django_db
def test_integration_does_not_raise_exception_organization_moved(
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
    )

    try:
        am = AlertManagerAPIView()
        am.dispatch(alert_channel_key=alert_receive_channel.token)
        assert False
    except OrganizationMovedException:
        assert False
    except Exception:
        assert True


@pytest.mark.django_db
def test_integration_raises_exception_organization_moved(
    make_organization_and_region,
    make_alert_receive_channel,
):
    organization, region = make_organization_and_region()
    organization.save()

    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
    )

    try:
        am = AlertManagerAPIView()
        am.dispatch(alert_channel_key=alert_receive_channel.token)
        assert False
    except OrganizationMovedException as e:
        assert e.organization == organization


@patch("apps.user_management.middlewares.OrganizationMovedMiddleware.make_request")
@pytest.mark.django_db
def test_organization_moved_middleware(
    mocked_make_request,
    make_organization_and_region,
    make_alert_receive_channel,
):
    organization, region = make_organization_and_region()
    organization.save()

    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
    )

    expected_message = bytes(f"Redirected to {region.oncall_backend_url}", "utf-8")
    mocked_make_request.return_value = HttpResponse(expected_message, status=status.HTTP_200_OK)

    client = APIClient()
    url = reverse("integrations:alertmanager", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {"value": "test"}
    response = client.post(url, data, format="json")
    assert mocked_make_request.called
    assert response.content == expected_message
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_api_token_does_not_raise_exception_organization_moved(
    make_organization,
    make_user_for_organization,
    make_public_api_token,
):
    organization = make_organization()

    admin = make_user_for_organization(organization)
    _, token = make_public_api_token(admin, organization)

    try:
        api_auth = ApiTokenAuthentication()
        api_auth.authenticate_credentials(token)
        assert True
    except OrganizationMovedException:
        assert False


@pytest.mark.django_db
def test_api_token_raises_exception_organization_moved(
    make_organization_and_region,
    make_user_for_organization,
    make_public_api_token,
):
    organization, region = make_organization_and_region()
    organization.save()

    admin = make_user_for_organization(organization)
    _, token = make_public_api_token(admin, organization)

    try:
        api_auth = ApiTokenAuthentication()
        api_auth.authenticate_credentials(token)
        assert False
    except OrganizationMovedException as e:
        assert e.organization == organization


@pytest.mark.django_db
def test_schedule_export_token_does_not_raise_exception_organization_moved(
    make_organization,
    make_user_for_organization,
    make_public_api_token,
    make_schedule,
):
    organization = make_organization()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    admin = make_user_for_organization(organization)
    _, token = ScheduleExportAuthToken.create_auth_token(admin, organization, schedule)

    try:
        schedule_auth = ScheduleExportAuthentication()
        schedule_auth.authenticate_credentials(token, schedule.public_primary_key)
        assert True
    except OrganizationMovedException:
        assert False


@pytest.mark.django_db
def test_schedule_export_token_raises_exception_organization_moved(
    make_organization_and_region,
    make_user_for_organization,
    make_public_api_token,
    make_schedule,
):
    organization, region = make_organization_and_region()
    organization.save()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    admin = make_user_for_organization(organization)
    _, token = ScheduleExportAuthToken.create_auth_token(admin, organization, schedule)

    try:
        schedule_auth = ScheduleExportAuthentication()
        schedule_auth.authenticate_credentials(token, schedule.public_primary_key)
        assert False
    except OrganizationMovedException as e:
        assert e.organization == organization


@pytest.mark.django_db
def test_user_schedule_export_token_does_not_raise_exception_organization_moved(
    make_organization,
    make_user_for_organization,
    make_public_api_token,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    _, token = UserScheduleExportAuthToken.create_auth_token(admin, organization)

    try:
        user_schedule_auth = UserScheduleExportAuthentication()
        user_schedule_auth.authenticate_credentials(token, admin.public_primary_key)
        assert True
    except OrganizationMovedException:
        assert False


@pytest.mark.django_db
def test_user_schedule_export_token_raises_exception_organization_moved(
    make_organization_and_region,
    make_user_for_organization,
    make_public_api_token,
):
    organization, region = make_organization_and_region()
    organization.save()

    admin = make_user_for_organization(organization)
    _, token = UserScheduleExportAuthToken.create_auth_token(admin, organization)

    try:
        user_schedule_auth = UserScheduleExportAuthentication()
        user_schedule_auth.authenticate_credentials(token, admin.public_primary_key)
        assert False
    except OrganizationMovedException as e:
        assert e.organization == organization
