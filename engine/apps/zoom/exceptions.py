from typing import Optional


class ZoomAPIException(Exception):
    """Base exception for Zoom API errors."""

    def __init__(
        self,
        status: int,
        url: Optional[str] = None,
        msg: str = "Zoom API error",
        method: Optional[str] = None,
    ):
        self.status = status
        self.url = url
        self.msg = msg
        self.method = method
        super().__init__(f"Zoom API error: {msg} (status={status}, url={url}, method={method})")


class ZoomAPITokenInvalid(ZoomAPIException):
    """Exception raised when the Zoom API token is invalid or missing."""

    def __init__(self, msg: str = "Zoom API token is invalid or missing"):
        super().__init__(status=401, msg=msg)


class ZoomAPIRateLimitError(ZoomAPIException):
    """Exception raised when Zoom API rate limit is exceeded."""

    def __init__(self, msg: str = "Zoom API rate limit exceeded"):
        super().__init__(status=429, msg=msg)


class ZoomAPIChannelNotFoundError(ZoomAPIException):
    """Exception raised when a Zoom channel is not found."""

    def __init__(self, channel_id: str):
        super().__init__(status=404, msg=f"Channel {channel_id} not found")


class ZoomAPIUserNotFoundError(ZoomAPIException):
    """Exception raised when a Zoom user is not found."""

    def __init__(self, user_id: str):
        super().__init__(status=404, msg=f"User {user_id} not found")
