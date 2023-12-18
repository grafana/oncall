import pytest
from django.urls import reverse
from fcm_django.models import DeviceType
from rest_framework import status
from rest_framework.test import APIClient

from apps.mobile_app.models import FCMDevice


@pytest.mark.django_db
def test_create_update_fcm_device(make_organization_and_user_with_mobile_app_auth_token):
    organization, user, verification_token = make_organization_and_user_with_mobile_app_auth_token()
    registration_id = "test_registration_id"

    client = APIClient()
    url = reverse("mobile_app:fcm-list")

    # create new device
    data = {
        "registration_id": registration_id,
        "type": DeviceType.ANDROID,
        "name": "Test",
    }

    assert FCMDevice.objects.filter(registration_id=data["registration_id"]).count() == 0

    response = client.post(url, data=data, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()["registration_id"] == data["registration_id"]
    assert response.json()["type"] == data["type"]
    assert response.json()["name"] == data["name"]
    assert response.json()["active"] is True

    devices = FCMDevice.objects.filter(registration_id=data["registration_id"])
    assert devices.count() == 1
    device = devices.first()
    assert device.user == user

    # update using post and registration_id in data
    data["name"] = "Renamed"

    response = client.post(url, data=data, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["registration_id"] == data["registration_id"]
    assert response.json()["type"] == data["type"]
    assert response.json()["name"] == data["name"]
    assert response.json()["active"] is True

    assert FCMDevice.objects.filter(registration_id=data["registration_id"]).count() == 1
    device.refresh_from_db()
    assert device.user == user

    # update using put
    data["name"] = "Renamed2"
    data["active"] = False

    response = client.put(url + f"/{registration_id}", data=data, HTTP_AUTHORIZATION=verification_token)
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["registration_id"] == data["registration_id"]
    assert response.json()["type"] == data["type"]
    assert response.json()["name"] == data["name"]
    assert response.json()["active"] is False

    assert FCMDevice.objects.filter(registration_id=data["registration_id"]).count() == 1
    device.refresh_from_db()
    assert device.user == user


@pytest.mark.django_db
def test_fcm_device_multiple_users(
    make_organization_and_user_with_mobile_app_auth_token,
    make_organization_and_user,
    make_mobile_app_auth_token_for_user,
):
    _, user_1, verification_token_1 = make_organization_and_user_with_mobile_app_auth_token()
    organization_2, user_2 = make_organization_and_user()
    _, verification_token_2 = make_mobile_app_auth_token_for_user(user_2, organization_2)

    registration_id = "test_registration_id"

    client = APIClient()
    url = reverse("mobile_app:fcm-list")

    # create new device
    data = {
        "registration_id": registration_id,
        "type": DeviceType.ANDROID,
        "name": "Test",
    }

    assert FCMDevice.objects.filter(registration_id=data["registration_id"]).count() == 0
    # create device for user_1
    response = client.post(url, data=data, HTTP_AUTHORIZATION=verification_token_1)
    assert response.status_code == status.HTTP_201_CREATED

    devices = FCMDevice.objects.filter(registration_id=data["registration_id"])
    assert devices.count() == 1
    device_1 = devices.filter(user=user_1).first()
    assert device_1 is not None

    # create device for user_2
    response = client.post(url, data=data, HTTP_AUTHORIZATION=verification_token_2)
    assert response.status_code == status.HTTP_201_CREATED

    devices = FCMDevice.objects.filter(registration_id=data["registration_id"])
    assert devices.count() == 2
    device_2 = devices.filter(user=user_2).first()
    assert device_2 is not None

    # Check that the both devices are active and device_1 was not changed
    device_1.refresh_from_db()
    assert device_1.active is True
    assert device_2.active is True
    assert device_1.user == user_1

    # update device_1 using post and registration_id in data
    data_to_update = data.copy()
    data_to_update["name"] = "Renamed"

    response = client.post(url, data=data_to_update, HTTP_AUTHORIZATION=verification_token_1)
    assert response.status_code == status.HTTP_200_OK

    # Check that device_2 was not changed
    device_2.refresh_from_db()
    assert device_2.active is True
    assert device_2.name == data["name"]
    assert device_2.user == user_2

    # update device_2 using put
    data_to_update["name"] = "Renamed2"
    data_to_update["active"] = False

    response = client.put(url + f"/{registration_id}", data=data_to_update, HTTP_AUTHORIZATION=verification_token_2)
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["name"] == data_to_update["name"]
    assert response.json()["active"] is False

    device_2.refresh_from_db()
    assert device_2.active is False
    assert device_2.name == data_to_update["name"]
    assert device_2.user == user_2

    # Check that device_1 was not changed
    device_1.refresh_from_db()
    assert device_1.active is True
    assert device_1.name != data_to_update["name"]
    assert device_1.user == user_1

    # Delete device_1
    response = client.delete(url + f"/{registration_id}", HTTP_AUTHORIZATION=verification_token_1)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(FCMDevice.DoesNotExist):
        device_1.refresh_from_db()

    # Check that device_2 was not changed
    device_2.refresh_from_db()
    assert device_2.active is False
    assert device_2.name == data_to_update["name"]
    assert device_2.user == user_2


@pytest.mark.django_db
def test_fcm_device_owner(
    make_organization_and_user_with_mobile_app_auth_token,
    make_organization_and_user,
    make_mobile_app_auth_token_for_user,
):
    _, user_1, verification_token_1 = make_organization_and_user_with_mobile_app_auth_token()
    organization_2, user_2 = make_organization_and_user()
    _, verification_token_2 = make_mobile_app_auth_token_for_user(user_2, organization_2)

    registration_id = "test_registration_id"
    client = APIClient()
    url = reverse("mobile_app:fcm-list")

    device = FCMDevice.objects.create(registration_id=registration_id, user=user_2)

    response = client.get(url, HTTP_AUTHORIZATION=verification_token_1)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0

    response = client.get(url, HTTP_AUTHORIZATION=verification_token_2)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

    response = client.get(url + f"/{registration_id}", HTTP_AUTHORIZATION=verification_token_1)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.get(url + f"/{registration_id}", HTTP_AUTHORIZATION=verification_token_2)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["registration_id"] == registration_id

    response = client.delete(url + f"/{registration_id}", HTTP_AUTHORIZATION=verification_token_1)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    device.refresh_from_db()

    response = client.delete(url + f"/{registration_id}", HTTP_AUTHORIZATION=verification_token_2)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    with pytest.raises(FCMDevice.DoesNotExist):
        device.refresh_from_db()
