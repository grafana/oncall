import typing


class GoogleOauth2Response(typing.TypedDict):
    sub: str
    scope: str
    access_token: str
    refresh_token: typing.Optional[str]
    """
    NOTE: I think `refresh_token` is only included when the user initially grants access to our Google OAuth2 app
    on subsequent logins, the `refresh_token` is not included in the response, only `access_token`

    https://medium.com/starthinker/google-oauth-2-0-access-token-and-refresh-token-explained-cccf2fc0a6d9
    """
