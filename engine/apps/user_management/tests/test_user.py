import pytest

from apps.api.permissions import LegacyAccessControlRole
from apps.user_management.models import User


@pytest.mark.django_db
def test_self_or_admin(make_organization, make_user_for_organization):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    second_admin = make_user_for_organization(organization)
    editor = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)

    another_organization = make_organization()
    admin_from_another_organization = make_user_for_organization(another_organization)

    assert admin.self_or_admin(admin, organization) is True
    assert admin.self_or_admin(editor, organization) is False
    assert admin.self_or_admin(second_admin, organization) is True
    assert admin.self_or_admin(admin_from_another_organization, organization) is False


@pytest.mark.django_db
def test_lower_email_filter(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization, email="TestingUser@test.com")
    make_user_for_organization(organization, email="testing_user@test.com")

    assert User.objects.get(email__lower="testinguser@test.com") == user
    assert User.objects.filter(email__lower__in=["testinguser@test.com"]).get() == user
