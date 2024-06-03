REDIRECT_AFTER_SLACK_INSTALL = "redirect_after_slack_install"
# slack errors flags
SLACK_AUTH_WRONG_WORKSPACE_ERROR = "wrong_workspace"
SLACK_AUTH_SLACK_USER_ALREADY_CONNECTED_ERROR = "user_already_connected"
SLACK_AUTH_FAILED = "auth_failed"


# Example of a slack oauth response to be used in tests.
# It contains NO actual tokens, got it from slack docs.
# https://api.slack.com/authentication/oauth-v2
SLACK_OAUTH_ACCESS_RESPONSE = {
    "ok": True,
    "access_token": "xoxb-17653672481-19874698323-pdFZKVeTuE8sk7oOcBrzbqgy",
    "token_type": "bot",
    "scope": "commands,incoming-webhook",
    "bot_user_id": "U0KRQLJ9H",
    "app_id": "A0KRD7HC3",
    "team": {"name": "Slack Softball Team", "id": "T9TK3CUKW"},
    "enterprise": {"name": "slack-sports", "id": "E12345678"},
    "authed_user": {"id": "U1234", "scope": "chat:write", "access_token": "xoxp-1234", "token_type": "user"},
}
