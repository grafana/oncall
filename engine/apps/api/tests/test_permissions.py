import typing

import pytest
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin

from apps.api.permissions import (
    BASIC_ROLE_PERMISSIONS_ATTR,
    RBAC_PERMISSIONS_ATTR,
    BasicRolePermission,
    BasicRolePermissionsAttribute,
    GrafanaAPIPermissions,
    HasRBACPermissions,
    IsOwner,
    IsOwnerOrHasRBACPermissions,
    LegacyAccessControlRole,
    RBACObjectPermissionsAttribute,
    RBACPermission,
    RBACPermissionsAttribute,
    get_most_authorized_role,
    get_view_action,
    user_has_minimum_required_basic_role,
    user_is_authorized,
)
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
        rbac_permissions: typing.Optional[RBACPermissionsAttribute] = None,
        rbac_object_permissions: typing.Optional[RBACObjectPermissionsAttribute] = None,
        basic_role_permissions: typing.Optional[BasicRolePermissionsAttribute] = None,
    ) -> None:
        super().__init__()
        self.action = action

        if rbac_permissions:
            self.rbac_permissions = rbac_permissions
        if rbac_object_permissions:
            self.rbac_object_permissions = rbac_object_permissions
        if basic_role_permissions:
            self.basic_role_permissions = basic_role_permissions


class MockedAPIView(APIView):
    def __init__(
        self,
        rbac_permissions: typing.Optional[RBACPermissionsAttribute] = None,
        rbac_object_permissions: typing.Optional[RBACObjectPermissionsAttribute] = None,
        basic_role_permissions: typing.Optional[BasicRolePermissionsAttribute] = None,
    ) -> None:
        super().__init__()

        if rbac_permissions:
            self.rbac_permissions = rbac_permissions
        if rbac_object_permissions:
            self.rbac_object_permissions = rbac_object_permissions
        if basic_role_permissions:
            self.basic_role_permissions = basic_role_permissions


class TestLegacyAccessControlCompatiblePermission:
    @pytest.mark.parametrize(
        "permission_to_test,user_permission_prefix,user_basic_role,org_has_rbac_enabled,expected_result",
        [
            # rbac enabled
            (
                RBACPermission.Permissions.ALERT_GROUPS_READ,
                PluginID.ONCALL,
                LegacyAccessControlRole.VIEWER,
                True,
                True,
            ),
            (
                RBACPermission.Permissions.ALERT_GROUPS_WRITE,
                PluginID.ONCALL,
                LegacyAccessControlRole.VIEWER,
                True,
                False,
            ),
            # rbac enabled - cross-plugin prefixed permissions work
            (
                RBACPermission.Permissions.ALERT_GROUPS_READ,
                PluginID.IRM,
                LegacyAccessControlRole.VIEWER,
                True,
                True,
            ),
            # rbac disabled
            (
                RBACPermission.Permissions.ALERT_GROUPS_READ,
                PluginID.ONCALL,
                LegacyAccessControlRole.VIEWER,
                False,
                True,
            ),
            (
                RBACPermission.Permissions.ALERT_GROUPS_WRITE,
                PluginID.ONCALL,
                LegacyAccessControlRole.VIEWER,
                False,
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
        user_permission_prefix,
        user_basic_role,
        org_has_rbac_enabled,
        expected_result,
    ):
        user_permissions = GrafanaAPIPermissions.construct_permissions([f"{user_permission_prefix}.alert-groups:read"])

        org = make_organization(is_rbac_permissions_enabled=org_has_rbac_enabled)
        user = make_user_for_organization(org, role=user_basic_role, permissions=user_permissions)

        assert permission_to_test.user_has_permission(user) == expected_result


@pytest.mark.parametrize(
    "user_permissions,required_permissions,org_has_rbac_enabled,expected_result",
    [
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            True,
            True,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            False,
            True,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            True,
            True,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            False,
            True,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            True,
            False,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            False,
            True,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            False,
            False,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
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
    org_has_rbac_enabled,
    expected_result,
) -> None:
    basic_role = get_most_authorized_role(user_permissions)

    org = make_organization(is_rbac_permissions_enabled=org_has_rbac_enabled)
    user = make_user_for_organization(
        org,
        role=basic_role,
        permissions=GrafanaAPIPermissions.construct_permissions([perm.value_oncall_app for perm in user_permissions]),
    )

    assert user_is_authorized(user, required_permissions) == expected_result


@pytest.mark.parametrize(
    "user_permissions",
    [
        GrafanaAPIPermissions.construct_permissions(
            [
                f"{PluginID.ONCALL}.alert-groups:read",
                f"{PluginID.ONCALL}.schedules:read",
            ]
        ),
        GrafanaAPIPermissions.construct_permissions(
            [
                f"{PluginID.IRM}.alert-groups:read",
                f"{PluginID.IRM}.schedules:read",
            ]
        ),
        GrafanaAPIPermissions.construct_permissions(
            [
                f"{PluginID.ONCALL}.alert-groups:read",
                f"{PluginID.IRM}.schedules:read",
            ]
        ),
    ],
)
@pytest.mark.django_db
def test_user_is_authorized_grafana_irm_app(make_organization, make_user_for_organization, user_permissions):
    org = make_organization(is_rbac_permissions_enabled=True)
    user = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=user_permissions)
    required_permissions = [
        RBACPermission.Permissions.ALERT_GROUPS_READ,
        RBACPermission.Permissions.SCHEDULES_READ,
    ]

    assert user_is_authorized(user, required_permissions) is True


@pytest.mark.parametrize(
    "permissions,expected_role",
    [
        ([RBACPermission.Permissions.ALERT_GROUPS_READ], RBACPermission.Permissions.ALERT_GROUPS_READ.fallback_role),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            RBACPermission.Permissions.ALERT_GROUPS_WRITE.fallback_role,
        ),
        (
            [
                RBACPermission.Permissions.USER_SETTINGS_READ,
                RBACPermission.Permissions.USER_SETTINGS_WRITE,
                RBACPermission.Permissions.USER_SETTINGS_ADMIN,
            ],
            RBACPermission.Permissions.USER_SETTINGS_ADMIN.fallback_role,
        ),
    ],
)
def test_get_most_authorized_role(permissions, expected_role) -> None:
    assert get_most_authorized_role(permissions) == expected_role


@pytest.mark.parametrize(
    "user_role,required_basic_role,expected_result",
    [
        (LegacyAccessControlRole.NONE, LegacyAccessControlRole.NONE, True),
        (LegacyAccessControlRole.NONE, LegacyAccessControlRole.VIEWER, False),
        (LegacyAccessControlRole.NONE, LegacyAccessControlRole.EDITOR, False),
        (LegacyAccessControlRole.NONE, LegacyAccessControlRole.ADMIN, False),
        (LegacyAccessControlRole.VIEWER, LegacyAccessControlRole.NONE, True),
        (LegacyAccessControlRole.VIEWER, LegacyAccessControlRole.VIEWER, True),
        (LegacyAccessControlRole.VIEWER, LegacyAccessControlRole.EDITOR, False),
        (LegacyAccessControlRole.VIEWER, LegacyAccessControlRole.ADMIN, False),
        (LegacyAccessControlRole.EDITOR, LegacyAccessControlRole.NONE, True),
        (LegacyAccessControlRole.EDITOR, LegacyAccessControlRole.VIEWER, True),
        (LegacyAccessControlRole.EDITOR, LegacyAccessControlRole.EDITOR, True),
        (LegacyAccessControlRole.EDITOR, LegacyAccessControlRole.ADMIN, False),
        (LegacyAccessControlRole.ADMIN, LegacyAccessControlRole.NONE, True),
        (LegacyAccessControlRole.ADMIN, LegacyAccessControlRole.VIEWER, True),
        (LegacyAccessControlRole.ADMIN, LegacyAccessControlRole.EDITOR, True),
        (LegacyAccessControlRole.ADMIN, LegacyAccessControlRole.ADMIN, True),
    ],
)
@pytest.mark.django_db
def test_user_has_minimum_required_basic_role(
    make_organization_and_user,
    user_role,
    required_basic_role,
    expected_result,
):
    _, user = make_organization_and_user(role=user_role)
    assert user_has_minimum_required_basic_role(user, required_basic_role) == expected_result


def test_get_view_action():
    viewset_action = "viewset_action"
    viewset = MockedViewSet(viewset_action)

    apiview = MockedAPIView()

    method = "APIVIEW_ACTION"
    request = MockedRequest(method=method)

    assert get_view_action(request, viewset) == viewset_action, "it works with a ViewSet"
    assert get_view_action(request, apiview) == method.lower(), "it works with an APIView"


class TestRBACPermission:
    @pytest.mark.django_db
    def test_has_permission_works_on_a_viewset_view(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        required_permission = RBACPermission.Permissions.ALERT_GROUPS_READ

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
            role=LegacyAccessControlRole.NONE,
            permissions=GrafanaAPIPermissions.construct_permissions([required_permission.value_oncall_app]),
        )
        user_without_permission = make_user_for_organization(
            org,
            role=LegacyAccessControlRole.NONE,
            permissions=GrafanaAPIPermissions.construct_permissions(
                [RBACPermission.Permissions.ALERT_GROUPS_WRITE.value_oncall_app]
            ),
        )

        assert (
            RBACPermission().has_permission(MockedRequest(user_with_permission), viewset) is True
        ), "it works on a viewset when the user does have permission"

        assert (
            RBACPermission().has_permission(MockedRequest(user_without_permission), viewset) is False
        ), "it works on a viewset when the user does have permission"

        assert (
            RBACPermission().has_permission(
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
        required_permission = RBACPermission.Permissions.ALERT_GROUPS_READ

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
            role=LegacyAccessControlRole.NONE,
            permissions=GrafanaAPIPermissions.construct_permissions([required_permission.value_oncall_app]),
        )
        user2 = make_user_for_organization(
            org,
            role=LegacyAccessControlRole.NONE,
            permissions=GrafanaAPIPermissions.construct_permissions(
                [RBACPermission.Permissions.ALERT_GROUPS_WRITE.value_oncall_app]
            ),
        )

        class Request(MockedRequest):
            def __init__(self, user: typing.Optional[User] = None) -> None:
                super().__init__(user, method)

        assert (
            RBACPermission().has_permission(Request(user1), apiview) is True
        ), "it works on an APIView when the user has permission"

        assert (
            RBACPermission().has_permission(Request(user2), apiview) is False
        ), "it works on an APIView when the user does not have permission"

        assert (
            RBACPermission().has_permission(Request(user2), apiview_with_no_permissions) is True
        ), "it works on a viewset when the viewset action does not require permissions"

    def test_has_permission_throws_assertion_error_if_developer_forgets_to_specify_rbac_permissions(self) -> None:
        action_slash_method = "hello"
        error_msg = (
            f"Must define a {RBAC_PERMISSIONS_ATTR} dict on the ViewSet that is consuming the RBACPermission class"
        )

        viewset = MockedViewSet(action_slash_method)
        apiview = MockedAPIView()

        with pytest.raises(AssertionError, match=error_msg):
            RBACPermission().has_permission(MockedRequest(), viewset)

        with pytest.raises(AssertionError, match=error_msg):
            RBACPermission().has_permission(MockedRequest(method=action_slash_method), apiview)

    def test_has_permission_throws_assertion_error_if_developer_forgets_to_specify_an_action_in_rbac_permissions(
        self,
    ) -> None:
        action_slash_method = "hello"
        other_action_rbac_permissions = {"bonjour": []}
        error_msg = f"""Each action must be defined within the {RBAC_PERMISSIONS_ATTR} dict on the ViewSet.
\nIf an action requires no permissions, its value should explicitly be set to an empty list"""

        viewset = MockedViewSet(action_slash_method, other_action_rbac_permissions)
        apiview = MockedAPIView(rbac_permissions=other_action_rbac_permissions)

        with pytest.raises(AssertionError, match=error_msg):
            RBACPermission().has_permission(MockedRequest(), viewset)

        with pytest.raises(AssertionError, match=error_msg):
            RBACPermission().has_permission(MockedRequest(method=action_slash_method), apiview)

    def test_has_object_permission_returns_true_if_rbac_object_permissions_not_specified(self) -> None:
        request = MockedRequest()
        assert RBACPermission().has_object_permission(request, MockedAPIView(), None) is True
        assert RBACPermission().has_object_permission(request, MockedViewSet("potato"), None) is True

    def test_has_object_permission_works_if_no_permission_class_specified_for_action(self) -> None:
        action = "hello"

        request = MockedRequest(None, action)
        apiview = MockedAPIView(rbac_object_permissions={})
        viewset = MockedViewSet(action, rbac_object_permissions={})

        assert RBACPermission().has_object_permission(request, apiview, None) is True
        assert RBACPermission().has_object_permission(request, viewset, None) is True

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

        assert RBACPermission().has_object_permission(request, apiview, None) is True
        assert RBACPermission().has_object_permission(request, viewset, None) is True

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

        assert RBACPermission().has_object_permission(request, apiview, None) == mocked_permission_class_response
        assert RBACPermission().has_object_permission(request, viewset, None) == mocked_permission_class_response


class TestIsOwner:
    @pytest.mark.django_db
    def test_it_works_when_comparing_user_to_object(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])

        request = MockedRequest(user1)
        IsUser = IsOwner()

        assert IsUser.has_object_permission(request, None, user1) is True
        assert IsUser.has_object_permission(request, None, user2) is False

    @pytest.mark.django_db
    def test_it_works_when_comparing_user_to_ownership_field_object(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])

        schedule = MockedSchedule(user1)
        IsScheduleOwner = IsOwner("user")

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
        user1 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])

        schedule = MockedSchedule(user1)
        thingy = Thingy(schedule)
        IsScheduleOwner = IsOwner("schedule.user")

        assert IsScheduleOwner.has_object_permission(MockedRequest(user1), None, thingy) is True
        assert IsScheduleOwner.has_object_permission(MockedRequest(user2), None, thingy) is False


@pytest.mark.parametrize(
    "user_permissions,required_permissions,expected_result",
    [
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            True,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            True,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            False,
        ),
        (
            [RBACPermission.Permissions.ALERT_GROUPS_READ],
            [RBACPermission.Permissions.ALERT_GROUPS_READ, RBACPermission.Permissions.ALERT_GROUPS_WRITE],
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
        role=LegacyAccessControlRole.NONE,
        permissions=GrafanaAPIPermissions.construct_permissions([perm.value_oncall_app for perm in user_permissions]),
    )

    request = MockedRequest(user)
    assert HasRBACPermissions(required_permissions).has_object_permission(request, None, None) == expected_result


class TestIsOwnerOrHasRBACPermissions:
    required_permission = RBACPermission.Permissions.SCHEDULES_READ
    required_permissions = [required_permission]
    user_permissions = GrafanaAPIPermissions.construct_permissions(
        [perm.value_oncall_app for perm in required_permissions]
    )

    @pytest.mark.django_db
    def test_it_works_when_user_is_owner_and_does_not_have_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])
        schedule = MockedSchedule(user1)
        request = MockedRequest(user1)

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is True

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is True

    @pytest.mark.django_db
    def test_it_works_when_user_is_owner_and_has_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=self.user_permissions)
        schedule = MockedSchedule(user1)
        request = MockedRequest(user1)

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is True

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is True

    @pytest.mark.django_db
    def test_it_works_when_user_is_not_owner_and_does_not_have_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])

        schedule = MockedSchedule(user1)
        request = MockedRequest(user2)

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is False

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is False

    @pytest.mark.django_db
    def test_it_works_when_user_is_not_owner_and_has_permissions(
        self,
        make_organization,
        make_user_for_organization,
    ) -> None:
        org = make_organization(is_rbac_permissions_enabled=True)
        user1 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])
        user2 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=self.user_permissions)
        user3 = make_user_for_organization(org, role=LegacyAccessControlRole.NONE, permissions=[])

        schedule = MockedSchedule(user1)
        request = MockedRequest(user2)
        request_user3 = MockedRequest(user3)

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions)
        assert PermClass.has_object_permission(request, None, user1) is True

        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions, "user")
        assert PermClass.has_object_permission(request, None, schedule) is True

        class Thingy:
            def __init__(self, schedule: MockedSchedule) -> None:
                self.schedule = schedule

        thingy = Thingy(schedule)
        PermClass = IsOwnerOrHasRBACPermissions(self.required_permissions, "schedule.user")

        assert PermClass.has_object_permission(request, None, thingy) is True
        assert PermClass.has_object_permission(request_user3, None, thingy) is False


class TestBasicRolePermission:
    @pytest.mark.django_db
    def test_has_permission_works_on_a_viewset_view(
        self,
        make_organization_and_user,
        make_user_for_organization,
    ) -> None:
        required_role = LegacyAccessControlRole.VIEWER

        action = "hello"
        viewset = MockedViewSet(
            action=action,
            basic_role_permissions={
                action: required_role,
            },
        )

        org, user_with_permission = make_organization_and_user(role=required_role)
        user_without_permission = make_user_for_organization(org, role=LegacyAccessControlRole.NONE)

        assert (
            BasicRolePermission().has_permission(MockedRequest(user_with_permission), viewset) is True
        ), "it works on a viewset when the user does have permission"

        assert (
            BasicRolePermission().has_permission(MockedRequest(user_without_permission), viewset) is False
        ), "it works on a viewset when the user does have permission"

    @pytest.mark.django_db
    def test_has_permission_works_on_an_apiview_view(
        self,
        make_organization_and_user,
        make_user_for_organization,
    ) -> None:
        required_role = LegacyAccessControlRole.VIEWER

        method = "hello"
        apiview = MockedAPIView(
            basic_role_permissions={
                method: required_role,
            },
        )

        org, user_with_permission = make_organization_and_user(role=required_role)
        user_without_permission = make_user_for_organization(org, role=LegacyAccessControlRole.NONE)

        class Request(MockedRequest):
            def __init__(self, user: typing.Optional[User] = None) -> None:
                super().__init__(user, method)

        assert (
            BasicRolePermission().has_permission(Request(user_with_permission), apiview) is True
        ), "it works on an APIView when the user has permission"

        assert (
            BasicRolePermission().has_permission(Request(user_without_permission), apiview) is False
        ), "it works on an APIView when the user does not have permission"

    def test_has_permission_throws_assertion_error_if_developer_forgets_to_specify_basic_role_permissions(self) -> None:
        action_slash_method = "hello"
        error_msg = f"Must define a {BASIC_ROLE_PERMISSIONS_ATTR} dict on the ViewSet that is consuming the role class"

        viewset = MockedViewSet(action_slash_method)
        apiview = MockedAPIView()

        with pytest.raises(AssertionError, match=error_msg):
            BasicRolePermission().has_permission(MockedRequest(), viewset)

        with pytest.raises(AssertionError, match=error_msg):
            BasicRolePermission().has_permission(MockedRequest(method=action_slash_method), apiview)

    def test_has_permission_throws_assertion_error_if_developer_forgets_to_specify_an_action_in_basic_role_permissions(
        self,
    ) -> None:
        action_slash_method = "hello"
        other_action_role_permissions = {"bonjour": LegacyAccessControlRole.VIEWER}
        error_msg = f"""Each action must be defined within the {BASIC_ROLE_PERMISSIONS_ATTR} dict on the ViewSet"""

        viewset = MockedViewSet(action_slash_method, basic_role_permissions=other_action_role_permissions)
        apiview = MockedAPIView(basic_role_permissions=other_action_role_permissions)

        with pytest.raises(AssertionError, match=error_msg):
            BasicRolePermission().has_permission(MockedRequest(), viewset)

        with pytest.raises(AssertionError, match=error_msg):
            BasicRolePermission().has_permission(MockedRequest(method=action_slash_method), apiview)

    def test_has_object_permission_returns_true(self) -> None:
        action = "hello"

        request = MockedRequest(None, action)
        apiview = MockedAPIView()
        viewset = MockedViewSet(action)

        assert BasicRolePermission().has_object_permission(request, apiview, None) is True
        assert BasicRolePermission().has_object_permission(request, viewset, None) is True
