from urllib.parse import urljoin

from social_core.backends.slack import SlackOAuth2
from social_core.utils import handle_http_errors

from apps.auth_token.constants import SLACK_AUTH_TOKEN_NAME
from apps.auth_token.models import SlackAuthToken

# Scopes for slack user token.
# It is main purpose - retrieve user data in SlackOAuth2V2 but we are using it in legacy code or weird Slack api cases.
USER_SCOPE = ["channels:read", "identify", "chat:write", "users.profile:read", "users:read", "users:read.email"]

# Scopes for slack bot token.
# Is is prime token we are using for most requests to Slack api.
# Changing these scopes requires confirmation in Slack app settings.
BOT_SCOPE = [
    "app_mentions:read",
    "channels:history",
    "channels:join",
    "channels:read",
    "chat:write",
    "chat:write.customize",
    "chat:write.public",
    "commands",
    "files:write",
    "groups:history",
    "groups:read",
    "im:history",
    "im:read",
    "im:write",
    "mpim:history",
    "reactions:write",
    "team:read",
    "usergroups:read",
    "usergroups:write",
    "users.profile:read",
    "users:read",
    "users:read.email",
    "users:write",
]

# Reference to Slack tokens: https://api.slack.com/authentication/token-types


class SlackOAuth2V2(SlackOAuth2):
    """
    Slack app with granular permissions require using SlackOauth2.0 V2.
    SlackOAuth2V2 and its inheritors tune SlackOAuth2 implementation from social core to fit new endpoints
    and response shapes.
    Read more https://api.slack.com/authentication/oauth-v2
    """

    AUTHORIZATION_URL = "https://slack.com/oauth/v2/authorize"
    ACCESS_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
    AUTH_TOKEN_NAME = SLACK_AUTH_TOKEN_NAME

    # Remove redirect state because we lose session during redirects
    REDIRECT_STATE = False
    STATE_PARAMETER = False

    EXTRA_DATA = [("id", "id"), ("name", "name"), ("real_name", "real_name"), ("team", "team")]

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes login process, must return user instance"""
        self.process_error(self.data)
        state = self.validate_state()
        # add auth token to redirect uri, because it must be the same in all slack auth requests
        token_string = self.data.get(self.AUTH_TOKEN_NAME)
        if token_string:
            self._update_redirect_uri_with_auth_token(token_string)
        data, params = None, None
        if self.ACCESS_TOKEN_METHOD == "GET":
            params = self.auth_complete_params(state)
        else:
            data = self.auth_complete_params(state)

        response = self.request_access_token(
            self.access_token_url(),
            data=data,
            params=params,
            headers=self.auth_headers(),
            auth=self.auth_complete_credentials(),
            method=self.ACCESS_TOKEN_METHOD,
        )
        self.process_error(response)
        access_token = response["authed_user"]["access_token"]
        return self.do_auth(access_token, response=response, *args, **kwargs)

    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        data = self.user_data(access_token, *args, **kwargs)
        data.pop("team", None)  # we don't want to override team from token by team from user_data request
        response = kwargs.get("response") or {}
        response.update(data or {})
        if "access_token" not in response:
            response["access_token"] = access_token
        kwargs.update({"response": response, "backend": self})
        return self.strategy.authenticate(*args, **kwargs)

    def get_scope_argument(self):
        param = {}
        scopes = self.get_scope()
        for k, v in scopes.items():
            param[k] = self.SCOPE_SEPARATOR.join(v)
        return param

    def user_data(self, access_token, *args, **kwargs):
        """
        Override original method to load user data using method users.profile.get with users.profile:read scope
        """
        r = self.get_json("https://slack.com/api/users.profile.get", params={"token": access_token})
        if r["ok"] is False:
            r = self.get_json(
                "https://slack.com/api/users.profile.get",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        r = r["profile"]
        # Emulate shape of return value from original method to not to brake smth inside social_core
        response = {}
        response["user"] = {}
        response["user"]["name"] = r["real_name_normalized"]
        response["user"]["email"] = r["email"]
        response["team"] = r.get("team", None)
        return response

    def start(self):
        """Add slack auth token to redirect uri and continue authentication"""
        token_string = self._generate_auth_token_string()
        self._update_redirect_uri_with_auth_token(token_string)
        return super().start()

    def _generate_auth_token_string(self) -> str:
        _, token_string = SlackAuthToken.create_auth_token(
            self.strategy.request.user, self.strategy.request.auth.organization
        )
        return token_string

    def _update_redirect_uri_with_auth_token(self, token_string: str) -> None:
        auth_token_param = f"?{self.AUTH_TOKEN_NAME}={token_string}"
        self.redirect_uri = urljoin(self.redirect_uri, auth_token_param)


class LoginSlackOAuth2V2(SlackOAuth2V2):
    name = "slack-login"
    SCOPE_PARAMETER_NAME = "user_scope"

    EXTRA_DATA = [
        ("id", "id"),
        ("name", "name"),
        ("real_name", "real_name"),
        ("team", "team"),
    ]

    def get_scope(self):
        return {"user_scope": USER_SCOPE}


class InstallSlackOAuth2V2(SlackOAuth2V2):
    name = "slack-install-free"

    def get_scope(self):
        return {"user_scope": USER_SCOPE, "scope": BOT_SCOPE}
