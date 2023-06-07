from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient

from apps.api.urls import router as internal_api_router
from apps.public_api.urls import router as public_api_router


@pytest.mark.parametrize(
    "basename,viewset_class,action",
    [
        # Collect all detail actions from all viewsets registered in internal API router
        (basename, viewset_class, action)
        for _, viewset_class, basename in internal_api_router.registry
        for action in viewset_class.get_extra_actions()
        if action.detail
    ],
)
@pytest.mark.django_db
def test_internal_api_detail_actions_get_object(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, basename, viewset_class, action
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse(f"api-internal:{basename}-{action.url_name}", kwargs={"pk": "NONEXISTENT"})

    with patch.object(viewset_class, "get_object", side_effect=NotFound) as mock_get_object:
        method = list(action.mapping.keys())[0]  # get the first allowed method
        response = client.generic(path=url, method=method, **make_user_auth_headers(user, token))

    """
    If you see this errors in tests, make sure to call self.get_object() in action method that's added / changed.
    Call to self.get_object() must come before any additional checks. For example, call to self.get_object() must come
    before checking for request data that may result in 400 Bad Request (i.e. check for 404 must come before check for 400).
    This is required to ensure all detail actions are safe, consistent with each other and easily testable.
    """
    assert response.status_code == status.HTTP_404_NOT_FOUND, "check for 404 must come before any additional checks"
    assert (
        mock_get_object.call_count == 1
    ), f"self.get_object() must be called in {viewset_class.__class__.__name__}.{action.__name__}"


@pytest.mark.parametrize(
    "basename,viewset_class,action",
    [
        # Collect all detail actions from all viewsets registered in public API router
        (basename, viewset_class, action)
        for _, viewset_class, basename in public_api_router.registry
        for action in viewset_class.get_extra_actions()
        if action.detail and action.url_path not in getattr(viewset_class, "extra_actions_ignore_no_get_object", [])
    ],
)
@pytest.mark.django_db
def test_public_api_detail_actions_get_object(make_organization_and_user_with_token, basename, viewset_class, action):
    organization, user, token = make_organization_and_user_with_token()
    client = APIClient()

    url = reverse(f"api-public:{basename}-{action.url_name}", kwargs={"pk": "NONEXISTENT"})

    with patch.object(viewset_class, "get_object", side_effect=NotFound) as mock_get_object:
        method = list(action.mapping.keys())[0]  # get the first allowed method
        response = client.generic(path=url, method=method, HTTP_AUTHORIZATION=token)

    """
    If you see this errors in tests, make sure to call self.get_object() in action method that's added / changed.
    Call to self.get_object() must come before any additional checks. For example, call to self.get_object() must come
    before checking for request data that may result in 400 Bad Request (i.e. check for 404 must come before check for 400).
    This is required to ensure all detail actions are safe, consistent with each other and easily testable.
    In rare cases when self.get_object() is not needed (e.g. because object is identified by authentication class),
    pass "extra_actions_ignore_no_get_object" to viewset class. Actions listed in extra_actions_ignore_no_get_object
    will be ignored by this test.
    """
    assert response.status_code == status.HTTP_404_NOT_FOUND, "check for 404 must come before any additional checks"
    assert (
        mock_get_object.call_count == 1
    ), f"self.get_object() must be called in {viewset_class.__class__.__name__}.{action.__name__}"
