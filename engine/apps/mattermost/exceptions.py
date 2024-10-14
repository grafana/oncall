class MattermostAPITokenInvalid(Exception):
    pass


class MattermostAPIException(Exception):
    def __init__(self, status, url, msg="", method="GET"):
        self.url = url
        self.status = status
        self.method = method
        self.msg = msg

    def __str__(self) -> str:
        return f"MattermostAPIException: status={self.status} url={self.url} method={self.method} error={self.msg}"


class MattermostEventTokenInvalid(Exception):
    def __init__(self, msg=""):
        self.msg = msg

    def __str__(self):
        return f"MattermostEventTokenInvalid message={self.msg}"
