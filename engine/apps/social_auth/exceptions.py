class InstallMultiRegionSlackException(Exception):
    pass


class UserLoginOAuth2MattermostException(Exception):
    pass


GOOGLE_AUTH_MISSING_GRANTED_SCOPE_ERROR = "missing_granted_scope"
MATTERMOST_AUTH_FETCH_USER_ERROR = "failed_to_fetch_user"
