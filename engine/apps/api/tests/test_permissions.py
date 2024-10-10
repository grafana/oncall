import typing

import pytest
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin

from apps.api import permissions
from apps.user_management.models import User
from common.constants.plugin_ids import PluginID


class MockedSchedule:
    def __init__(self, user: User) -> None:
        self.user = user


class MockedRequest:
    def __init__(self, user: typing.Optional[User] = None, method: typing.Optional[str] = None) -> None:
        if user:
            self.user = user
        if method:
            self.method = method


class MockedViewSet(ViewSetMixin):
    def __init__(
        self,
        action: str,
        rbac_permissions: typing.Optional[permissions.RBACPermissionsAttribute] = None,
        rbac_object_permissions: typing.Optional[permissions.RBACObjectPermissionsAttribute] = None,
    ) -> None:
        super().__init__()
        self.action = action

        if rbac_permissions:
            self.rbac_permissions = rbac_permissions
        if rbac_object_permissions:
            self.rbac_object_permissions = rbac_object_permissions


class MockedAPIView(APIView):
    def __init__(
        self,
        rbac_permissions: typing.Optional[permissions.RBACPermissionsAttribute] = None,
        rbac_object_permissions: typing.Optional[permissions.RBACObjectPermissionsAttribute] = None,
    ) -> None:
        super().__init__()

        if rbac_permissions:
            self.rbac_permissions = rbac_permissions
        if rbac_object_permissions:
            self.rbac_object_permissions = rbac_object_permissions


class TestLegacyAccessControlCompatiblePermission:
    @pytest.mark.parametrize(
        "permission_to_test,user_basic_role,is_rbac_permissions_enabled,is_grafana_irm_enabled,expected_result",
        [
            # rbac enabled - is_grafana_irm_enabled disabled
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.LegacyAccessControlRole.VIEWER,
                True,
                False,
                True,
            ),
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
                permissions.LegacyAccessControlRole.VIEWER,
                True,
                False,
                False,
            ),
            # rbac enabled - is_grafana_irm_enabled enabled
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.LegacyAccessControlRole.VIEWER,
                True,
                True,
                True,
            ),
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
                permissions.LegacyAccessControlRole.VIEWER,
                True,
                True,
                False,
            ),
            # rbac disabled (and hence is_grafana_irm_enabled is irrelevant)
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.LegacyAccessControlRole.VIEWER,
                False,
                False,
                True,
            ),
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.LegacyAccessControlRole.VIEWER,
                False,
                True,
                True,
            ),
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
                permissions.LegacyAccessControlRole.VIEWER,
                False,
                False,
                False,
            ),
            (
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
                permissions.LegacyAccessControlRole.VIEWER,
                False,
                True,
                False,
            ),
        ],
    )
    @pytest.mark.django_db
    def test_user_has_permission(
        self,
        make_organization,
        make_user_for_organization,
        permission_to_test,
        user_basic_role,
        is_rbac_permissions_enabled,
        is_grafana_irm_enabled,
        expected_result,
    ):
        user_permission = permissions.RBACPermission.Permissions.ALERT_GROUPS_READ

        org = make_organization(
            is_rbac_permissions_enabled=is_rbac_permissions_enabled, is_grafana_irm_enabled=is_grafana_irm_enabled
        )
        user = make_user_for_organization(
            org,
            role=user_basic_role,
            permissions=permissions.GrafanaAPIPermissions.construct_permissions(
                [
                    permissions.convert_oncall_permission_to_irm(user_permission)
                    if is_grafana_irm_enabled
                    else user_permission.value
                ]
            ),
        )

        assert permission_to_test.user_has_permission(user) == expected_result


@pytest.mark.parametrize(
    "user_role,required_basic_role,expected_result",
    [
        (permissions.LegacyAccessControlRole.NONE, permissions.LegacyAccessControlRole.NONE, True),
        (permissions.LegacyAccessControlRole.NONE, permissions.LegacyAccessControlRole.VIEWER, False),
        (permissions.LegacyAccessControlRole.NONE, permissions.LegacyAccessControlRole.EDITOR, False),
        (permissions.LegacyAccessControlRole.NONE, permissions.LegacyAccessControlRole.ADMIN, False),
        (permissions.LegacyAccessControlRole.VIEWER, permissions.LegacyAccessControlRole.NONE, True),
        (permissions.LegacyAccessControlRole.VIEWER, permissions.LegacyAccessControlRole.VIEWER, True),
        (permissions.LegacyAccessControlRole.VIEWER, permissions.LegacyAccessControlRole.EDITOR, False),
        (permissions.LegacyAccessControlRole.VIEWER, permissions.LegacyAccessControlRole.ADMIN, False),
        (permissions.LegacyAccessControlRole.EDITOR, permissions.LegacyAccessControlRole.NONE, True),
        (permissions.LegacyAccessControlRole.EDITOR, permissions.LegacyAccessControlRole.VIEWER, True),
        (permissions.LegacyAccessControlRole.EDITOR, permissions.LegacyAccessControlRole.EDITOR, True),
        (permissions.LegacyAccessControlRole.EDITOR, permissions.LegacyAccessControlRole.ADMIN, False),
        (permissions.LegacyAccessControlRole.ADMIN, permissions.LegacyAccessControlRole.NONE, True),
        (permissions.LegacyAccessControlRole.ADMIN, permissions.LegacyAccessControlRole.VIEWER, True),
        (permissions.LegacyAccessControlRole.ADMIN, permissions.LegacyAccessControlRole.EDITOR, True),
        (permissions.LegacyAccessControlRole.ADMIN, permissions.LegacyAccessControlRole.ADMIN, True),
    ],
)
@pytest.mark.django_db
def test_user_has_minimum_required_basic_role(
    make_organization,
    make_user_for_organization,
    user_role,
    required_basic_role,
    expected_result,
):
    org = make_organization()
    user = make_user_for_organization(org, role=user_role, permissions=[])
    assert permissions.user_has_minimum_required_basic_role(user, required_basic_role) is expected_result


@pytest.mark.parametrize("is_grafana_irm_enabled", [True, False])
@pytest.mark.parametrize(
    "user_permissions,required_permissions,is_rbac_permissions_enabled,expected_result",
    [
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            True,
            True,
        ),
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            False,
            True,
        ),
        (
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            True,
            True,
        ),
        (
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            False,
            True,
        ),
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            True,
            False,
        ),
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            False,
            True,
        ),
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            False,
            False,
        ),
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            True,
            False,
        ),
    ],
)
@pytest.mark.django_db
def test_user_is_authorized(
    make_organization,
    make_user_for_organization,
    user_permissions,
    required_permissions,
    is_rbac_permissions_enabled,
    is_grafana_irm_enabled,
    expected_result,
) -> None:
    basic_role = permissions.get_most_authorized_role(user_permissions)

    org = make_organization(
        is_rbac_permissions_enabled=is_rbac_permissions_enabled, is_grafana_irm_enabled=is_grafana_irm_enabled
    )
    user = make_user_for_organization(
        org,
        role=basic_role,
        permissions=permissions.GrafanaAPIPermissions.construct_permissions(
            [
                permissions.convert_oncall_permission_to_irm(perm) if is_grafana_irm_enabled else perm.value
                for perm in user_permissions
            ]
        ),
    )

    assert permissions.user_is_authorized(user, required_permissions) == expected_result


@pytest.mark.parametrize(
    "user_permissions,expected_role",
    [
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            permissions.RBACPermission.Permissions.ALERT_GROUPS_READ.fallback_role,
        ),
        (
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE.fallback_role,
        ),
        (
            [
                permissions.RBACPermission.Permissions.USER_SETTINGS_READ,
                permissions.RBACPermission.Permissions.USER_SETTINGS_WRITE,
                permissions.RBACPermission.Permissions.USER_SETTINGS_ADMIN,
            ],
            permissions.RBACPermission.Permissions.USER_SETTINGS_ADMIN.fallback_role,
        ),
    ],
)
def test_get_most_authorized_role(user_permissions, expected_role) -> None:
    assert permissions.get_most_authorized_role(user_permissions) == expected_role


def test_get_view_action():
    viewset_action = "viewset_action"
    viewset = MockedViewSet(viewset_action)

    apiview = MockedAPIView()

    method = "APIVIEW_ACTION"
    request = MockedRequest(method=method)

    assert permissions.get_view_action(request, viewset) == viewset_action, "it works with a ViewSet"
    assert permissions.get_view_action(request, apiview) == method.lower(), "it works with an APIView"


class TestRBACPermission:
    @pytest.mark.django_db
    def test_has_permission_works_on_a_viewset_view(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        required_permission = permissions.RBACPermission.Permissions.ALERT_GROUPS_READ

        action = "hello"
        viewset = MockedViewSet(
            action=action,
            rbac_permissions={
                action: [required_permission],
            },
        )

        viewset_with_no_required_permissions = MockedViewSet(
            action=action,
            rbac_permissions={
                action: [],
            },
        )

        org = make_organization(is_rbac_permissions_enabled=True)
        user_with_permission = make_user_for_organization(
            org,
            role=permissions.LegacyAccessControlRole.NONE,
            permissions=permissions.GrafanaAPIPermissions.construct_permissions([required_permission.value]),
        )
        user_without_permission = make_user_for_organization(
            org,
            role=permissions.LegacyAccessControlRole.NONE,
            permissions=permissions.GrafanaAPIPermissions.construct_permissions(
                [permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE.value]
            ),
        )

        assert (
            permissions.RBACPermission().has_permission(MockedRequest(user_with_permission), viewset) is True
        ), "it works on a viewset when the user does have permission"

        assert (
            permissions.RBACPermission().has_permission(MockedRequest(user_without_permission), viewset) is False
        ), "it works on a viewset when the user does have permission"

        assert (
            permissions.RBACPermission().has_permission(
                MockedRequest(user_without_permission), viewset_with_no_required_permissions
            )
            is True
        ), "it works on a viewset when the viewset action does not require permissions"

    @pytest.mark.django_db
    def test_has_permission_works_on_an_apiview_view(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        required_permission = permissions.RBACPermission.Permissions.ALERT_GROUPS_READ

        method = "hello"
        apiview = MockedAPIView(
            rbac_permissions={
                method: [required_permission],
            }
        )
        apiview_with_no_permissions = MockedAPIView(
            rbac_permissions={
                method: [],
            }
        )

        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(
            org,
            role=permissions.LegacyAccessControlRole.NONE,
            permissions=permissions.GrafanaAPIPermissions.construct_permissions([required_permission.value]),
        )
        user2 = make_user_for_organization(
            org,
            role=permissions.LegacyAccessControlRole.NONE,
            permissions=permissions.GrafanaAPIPermissions.construct_permissions(
                [permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE.value]
            ),
        )

        class Request(MockedRequest):
            def __init__(self, user: typing.Optional[User] = None) -> None:
                super().__init__(user, method)

        assert (
            permissions.RBACPermission().has_permission(Request(user1), apiview) is True
        ), "it works on an APIView when the user has permission"

        assert (
            permissions.RBACPermission().has_permission(Request(user2), apiview) is False
        ), "it works on an APIView when the user does not have permission"

        assert (
            permissions.RBACPermission().has_permission(Request(user2), apiview_with_no_permissions) is True
        ), "it works on a viewset when the viewset action does not require permissions"

    def test_has_permission_throws_assertion_error_if_developer_forgets_to_specify_rbac_permissions(self) -> None:
        action_slash_method = "hello"
        error_msg = f"Must define a {permissions.RBAC_PERMISSIONS_ATTR} dict on the ViewSet that is consuming the RBACPermission class"

        viewset = MockedViewSet(action_slash_method)
        apiview = MockedAPIView()

        with pytest.raises(AssertionError, match=error_msg):
            permissions.RBACPermission().has_permission(MockedRequest(), viewset)

        with pytest.raises(AssertionError, match=error_msg):
            permissions.RBACPermission().has_permission(MockedRequest(method=action_slash_method), apiview)

    def test_has_permission_throws_assertion_error_if_developer_forgets_to_specify_an_action_in_rbac_permissions(
        self,
    ) -> None:
        action_slash_method = "hello"
        other_action_rbac_permissions = {"bonjour": []}
        error_msg = f"""Each action must be defined within the {permissions.RBAC_PERMISSIONS_ATTR} dict on the ViewSet.
\nIf an action requires no permissions, its value should explicitly be set to an empty list"""

        viewset = MockedViewSet(action_slash_method, other_action_rbac_permissions)
        apiview = MockedAPIView(rbac_permissions=other_action_rbac_permissions)

        with pytest.raises(AssertionError, match=error_msg):
            permissions.RBACPermission().has_permission(MockedRequest(), viewset)

        with pytest.raises(AssertionError, match=error_msg):
            permissions.RBACPermission().has_permission(MockedRequest(method=action_slash_method), apiview)

    def test_has_object_permission_returns_true_if_rbac_object_permissions_not_specified(self) -> None:
        request = MockedRequest()
        assert permissions.RBACPermission().has_object_permission(request, MockedAPIView(), None) is True
        assert permissions.RBACPermission().has_object_permission(request, MockedViewSet("potato"), None) is True

    def test_has_object_permission_works_if_no_permission_class_specified_for_action(self) -> None:
        action = "hello"

        request = MockedRequest(None, action)
        apiview = MockedAPIView(rbac_object_permissions={})
        viewset = MockedViewSet(action, rbac_object_permissions={})

        assert permissions.RBACPermission().has_object_permission(request, apiview, None) is True
        assert permissions.RBACPermission().has_object_permission(request, viewset, None) is True

    def test_has_object_permission_returns_true_if_action_omitted_from_rbac_object_permissions(self) -> None:
        action1 = "hello"
        action2 = "world"

        class MockedPermissionClass:
            def has_object_permission(self, _req, _view, _obj) -> None:
                return True

        rbac_object_permissions = {MockedPermissionClass(): (action1,)}

        # only action1 is specified in rbac_object_permissions, lets make a request with action2
        # we should get back authorized
        request = MockedRequest(None, action2)
        apiview = MockedAPIView(rbac_object_permissions=rbac_object_permissions)
        viewset = MockedViewSet(action2, rbac_object_permissions=rbac_object_permissions)

        assert permissions.RBACPermission().has_object_permission(request, apiview, None) is True
        assert permissions.RBACPermission().has_object_permission(request, viewset, None) is True

    def test_has_object_permission_works_when_permission_class_specified_for_action(self) -> None:
        action = "hello"
        mocked_permission_class_response = "asdfasdfasdf"

        class MockedPermissionClass:
            def has_object_permission(self, _req, _view, _obj) -> None:
                return mocked_permission_class_response

        rbac_object_permissions = {MockedPermissionClass(): (action,)}
        request = MockedRequest(None, action)
        apiview = MockedAPIView(rbac_object_permissions=rbac_object_permissions)
        viewset = MockedViewSet(action, rbac_object_permissions=rbac_object_permissions)

        assert (
            permissions.RBACPermission().has_object_permission(request, apiview, None)
            == mocked_permission_class_response
        )
        assert (
            permissions.RBACPermission().has_object_permission(request, viewset, None)
            == mocked_permission_class_response
        )


class TestIsOwner:
    @pytest.mark.django_db
    def test_it_works_when_comparing_user_to_object(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])

        request = MockedRequest(user1)
        IsUser = permissions.IsOwner()

        assert IsUser.has_object_permission(request, None, user1) is True
        assert IsUser.has_object_permission(request, None, user2) is False

    @pytest.mark.django_db
    def test_it_works_when_comparing_user_to_ownership_field_object(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])

        schedule = MockedSchedule(user1)
        IsScheduleOwner = permissions.IsOwner("user")

        assert IsScheduleOwner.has_object_permission(MockedRequest(user1), None, schedule) is True
        assert IsScheduleOwner.has_object_permission(MockedRequest(user2), None, schedule) is False

    @pytest.mark.django_db
    def test_it_works_when_comparing_user_to_nested_ownership_field_object(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        class Thingy:
            def __init__(self, schedule: MockedSchedule) -> None:
                self.schedule = schedule

        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])

        schedule = MockedSchedule(user1)
        thingy = Thingy(schedule)
        IsScheduleOwner = permissions.IsOwner("schedule.user")

        assert IsScheduleOwner.has_object_permission(MockedRequest(user1), None, thingy) is True
        assert IsScheduleOwner.has_object_permission(MockedRequest(user2), None, thingy) is False


@pytest.mark.parametrize(
    "user_permissions,required_permissions,expected_result",
    [
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            True,
        ),
        (
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            True,
        ),
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            False,
        ),
        (
            [permissions.RBACPermission.Permissions.ALERT_GROUPS_READ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            False,
        ),
    ],
)
@pytest.mark.django_db
def test_HasRBACPermission(
    make_organization,
    make_user_for_organization,
    user_permissions,
    required_permissions,
    expected_result,
) -> None:
    org = make_organization(is_rbac_permissions_enabled=True)
    user = make_user_for_organization(
        org,
        role=permissions.LegacyAccessControlRole.NONE,
        permissions=permissions.GrafanaAPIPermissions.construct_permissions([perm.value for perm in user_permissions]),
    )

    request = MockedRequest(user)
    assert (
        permissions.HasRBACPermissions(required_permissions).has_object_permission(request, None, None)
        == expected_result
    )


class TestIsOwnerOrHasRBACPermissions:
    required_permission = permissions.RBACPermission.Permissions.SCHEDULES_READ
    required_permissions = [required_permission]
    user_permissions = permissions.GrafanaAPIPermissions.construct_permissions(
        [perm.value for perm in required_permissions]
    )

    @pytest.mark.django_db
    def test_it_works_when_user_is_owner_and_does_not_have_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])
        schedule = MockedSchedule(user1)
        request = MockedRequest(user1)

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is True

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is True

    @pytest.mark.django_db
    def test_it_works_when_user_is_owner_and_has_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(
            org, role=permissions.LegacyAccessControlRole.NONE, permissions=self.user_permissions
        )
        schedule = MockedSchedule(user1)
        request = MockedRequest(user1)

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is True

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is True

    @pytest.mark.django_db
    def test_it_works_when_user_is_not_owner_and_does_not_have_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])
        schedule = MockedSchedule(user1)
        request = MockedRequest(user2)

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is False

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is False

    @pytest.mark.django_db
    def test_it_works_when_user_is_not_owner_and_has_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(
            org, role=permissions.LegacyAccessControlRole.NONE, permissions=self.user_permissions
        )
        user3 = make_user_for_organization(org, role=permissions.LegacyAccessControlRole.NONE, permissions=[])

        schedule = MockedSchedule(user1)
        request = MockedRequest(user2)
        request_user3 = MockedRequest(user3)

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is True

        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is True

        class Thingy:
            def __init__(self, schedule: MockedSchedule) -> None:
                self.schedule = schedule

        thingy = Thingy(schedule)
        PermClass = permissions.IsOwnerOrHasRBACPermissions(self.required_permissions, "schedule.user")

        assert PermClass.has_object_permission(request, None, thingy) is True
        assert PermClass.has_object_permission(request_user3, None, thingy) is False


@pytest.mark.parametrize(
    "permission,expected",
    [
        (
            permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
            f"{PluginID.IRM}.alert-groups:read",
        ),
        (
            permissions.RBACPermission.Permissions.LABEL_READ,
            permissions.RBACPermission.Permissions.LABEL_READ.value,
        ),
    ],
)
def test_convert_oncall_permission_to_irm(permission, expected) -> None:
    assert permissions.convert_oncall_permission_to_irm(permission) == expected


@pytest.mark.parametrize(
    "is_grafana_irm_enabled,required_permissions,expected_permission_values",
    [
        (
            False,
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ.value,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE.value,
            ],
        ),
        (
            True,
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE,
            ],
            [
                permissions.RBACPermission.Permissions.ALERT_GROUPS_READ.value.replace(PluginID.ONCALL, PluginID.IRM),
                permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE.value.replace(PluginID.ONCALL, PluginID.IRM),
            ],
        ),
        (
            True,
            [
                permissions.RBACPermission.Permissions.LABEL_CREATE,
                permissions.RBACPermission.Permissions.LABEL_WRITE,
                permissions.RBACPermission.Permissions.LABEL_READ,
            ],
            [
                permissions.RBACPermission.Permissions.LABEL_CREATE.value,
                permissions.RBACPermission.Permissions.LABEL_WRITE.value,
                permissions.RBACPermission.Permissions.LABEL_READ.value,
            ],
        ),
    ],
)
@pytest.mark.django_db
def test_get_required_permission_values(
    make_organization,
    is_grafana_irm_enabled,
    required_permissions,
    expected_permission_values,
) -> None:
    organization = make_organization(is_rbac_permissions_enabled=True, is_grafana_irm_enabled=is_grafana_irm_enabled)
    assert permissions.get_required_permission_values(organization, required_permissions) == expected_permission_values


@pytest.mark.parametrize(
    "perm,expected_permission",
    [
        (
            permissions.RBACPermission.Permissions.ALERT_GROUPS_READ.value,
            permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
        ),
        (
            "non.existent.permission",
            None,
        ),
        (
            permissions.convert_oncall_permission_to_irm(permissions.RBACPermission.Permissions.ALERT_GROUPS_READ),
            permissions.RBACPermission.Permissions.ALERT_GROUPS_READ,
        ),
    ],
)
def test_all_permission_name_to_class_map(perm, expected_permission) -> None:
    assert permissions.ALL_PERMISSION_NAME_TO_CLASS_MAP.get(perm, None) == expected_permission
