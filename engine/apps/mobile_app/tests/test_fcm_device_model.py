import pytest
from django.core.exceptions import MultipleObjectsReturned

from apps.mobile_app.models import FCMDevice


@pytest.mark.django_db
def test_get_active_device_for_user_works(make_organization_and_user):
    _, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="inactive_device_id", active=False)
    active_device = FCMDevice.objects.create(user=user, registration_id="active_device_id", active=True)

    assert FCMDevice.objects.filter(user=user).count() == 2
    assert FCMDevice.get_active_device_for_user(user) == active_device

    # if the user has two active devices, django will complain. however, we "should" never get to this
    # case because we have the ONE_DEVICE_PER_USER FCM django setting set to True
    _, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="active_device_1")
    FCMDevice.objects.create(user=user, registration_id="active_device_2")

    with pytest.raises(MultipleObjectsReturned):
        FCMDevice.get_active_device_for_user(user)
